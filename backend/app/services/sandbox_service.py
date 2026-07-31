import os
import time
import resource
import asyncio
import hashlib
import tempfile
import logging
import ast as python_ast
from pathlib import Path
from typing import Optional, Dict, Any
from app.models.schemas import ExecutionResult
from app.core.config import settings
from app.core.metrics import EXECUTION_DURATION, EXECUTION_BLOCKED

logger = logging.getLogger("nexagrid.sandbox")

class ExecutionSandbox:
    """
    Isolated Code Execution Engine.
    Defense in depth layers:
    1. Static AST Security Analysis (Python ast module walking node trees for imports, builtins, and dangerous methods)
    2. Subprocess isolation (independent child process)
    3. POSIX resource limit enforcement (CPU time, memory, file descriptors, max processes)
    4. Timeout enforcement (asyncio.wait_for)
    5. Temporary execution directory isolation
    """
    
    SUPPORTED_LANGUAGES = {
        "python": {"runner": "python3", "extension": ".py"},
        "javascript": {"runner": "node", "extension": ".js"},
        "go": {"runner": "go run", "extension": ".go"},
    }

    BLOCKED_PATTERNS = {
        "javascript": [
            "require('fs')", 'require("fs")', "require('child_process')",
            'require("child_process")', "process.exit", "eval(", "Function("
        ],
        "go": [
            "os/exec", "syscall", "unsafe"
        ]
    }

    async def execute(
        self,
        code: str,
        language: str = "python",
        stdin: Optional[str] = None
    ) -> ExecutionResult:
        language = language.lower()
        if language not in self.SUPPORTED_LANGUAGES:
            return ExecutionResult(
                stdout="",
                stderr=f"Language '{language}' is not supported.",
                exit_code=-1,
                execution_time_ms=0,
                blocked=True
            )

        # 1. Static Security Analysis (Real AST Analysis for Python)
        blocked_reason = self._check_dangerous_code(code, language)
        if blocked_reason:
            EXECUTION_BLOCKED.labels(reason=blocked_reason, language=language).inc()
            return ExecutionResult(
                stdout="",
                stderr=f"Security Policy Violation: Execution blocked due to unsafe code pattern ({blocked_reason}).",
                exit_code=-1,
                execution_time_ms=0,
                blocked=True,
                metadata={"blocked_pattern": blocked_reason}
            )

        lang_config = self.SUPPORTED_LANGUAGES[language]
        start_time = time.perf_counter()

        with tempfile.TemporaryDirectory() as tmpdir:
            code_file = Path(tmpdir) / f"main{lang_config['extension']}"
            code_file.write_text(code, encoding="utf-8")

            try:
                # 2. Subprocess Execution with OS Resource Limits
                process = await asyncio.create_subprocess_exec(
                    *lang_config["runner"].split(),
                    str(code_file),
                    stdin=asyncio.subprocess.PIPE if stdin else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir,
                    preexec_fn=self._set_posix_limits
                )

                # 3. Timeout Enforcement
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin.encode() if stdin else None),
                    timeout=settings.EXECUTION_TIMEOUT_SECONDS
                )

                execution_time_sec = time.perf_counter() - start_time
                execution_time_ms = round(execution_time_sec * 1000, 2)
                EXECUTION_DURATION.labels(language=language).observe(execution_time_sec)

                stdout_text = stdout[:settings.MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
                stderr_text = stderr[:settings.MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")

                code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()

                return ExecutionResult(
                    stdout=stdout_text,
                    stderr=stderr_text,
                    exit_code=process.returncode,
                    execution_time_ms=execution_time_ms,
                    blocked=False,
                    metadata={
                        "code_hash": code_hash,
                        "memory_limit_mb": settings.MAX_MEMORY_MB,
                        "timeout_seconds": settings.EXECUTION_TIMEOUT_SECONDS,
                        "output_bytes": len(stdout_text) + len(stderr_text)
                    }
                )

            except asyncio.TimeoutError:
                if 'process' in locals():
                    try:
                        process.kill()
                    except Exception:
                        pass
                EXECUTION_BLOCKED.labels(reason="timeout", language=language).inc()
                return ExecutionResult(
                    stdout="",
                    stderr=f"Time Limit Exceeded: Execution timed out after {settings.EXECUTION_TIMEOUT_SECONDS}s.",
                    exit_code=-1,
                    execution_time_ms=settings.EXECUTION_TIMEOUT_SECONDS * 1000,
                    blocked=True,
                    metadata={"error": "TIMEOUT"}
                )
            except Exception as e:
                logger.error(f"Execution error: {e}")
                return ExecutionResult(
                    stdout="",
                    stderr=f"Execution System Error: {str(e)}",
                    exit_code=-1,
                    execution_time_ms=0,
                    blocked=False
                )

    def _set_posix_limits(self):
        """Pre-exec hook setting POSIX resource limits on child process."""
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (5, 10))
            memory_bytes = settings.MAX_MEMORY_MB * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        except Exception:
            pass

    def _check_dangerous_code(self, code: str, language: str) -> Optional[str]:
        if language == "python":
            return self._ast_check_python(code)
        patterns = self.BLOCKED_PATTERNS.get(language, [])
        for pattern in patterns:
            if pattern in code:
                return pattern
        return None

    def _ast_check_python(self, code: str) -> Optional[str]:
        """Real AST-based security analysis for Python using stdlib ast module."""
        try:
            tree = python_ast.parse(code)
        except SyntaxError as e:
            return f"syntax_error:{e}"

        BLOCKED_MODULES = {
            "os", "subprocess", "socket", "sys", "pty", "shutil",
            "ctypes", "importlib", "pickle", "marshal"
        }
        BLOCKED_BUILTINS = {
            "eval", "exec", "__import__", "compile", "open",
            "breakpoint", "globals", "locals", "vars"
        }

        for node in python_ast.walk(tree):
            if isinstance(node, python_ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in BLOCKED_MODULES:
                        return f"blocked_import:{alias.name}"

            if isinstance(node, python_ast.ImportFrom):
                if node.module and node.module.split(".")[0] in BLOCKED_MODULES:
                    return f"blocked_import_from:{node.module}"

            if isinstance(node, python_ast.Call):
                if isinstance(node.func, python_ast.Name):
                    if node.func.id in BLOCKED_BUILTINS:
                        return f"blocked_builtin:{node.func.id}"
                if isinstance(node.func, python_ast.Attribute):
                    if node.func.attr in {"system", "popen", "spawn", "exec", "execv", "execl", "fork", "run", "call"}:
                        return f"blocked_method:{node.func.attr}"

        return None

sandbox_engine = ExecutionSandbox()
