import os
import time
import resource
import asyncio
import hashlib
import tempfile
import logging
import shutil
import ast as python_ast
from pathlib import Path
from typing import Optional, Dict, Any
from app.models.schemas import ExecutionResult
from app.core.metrics import EXECUTION_DURATION, EXECUTION_BLOCKED

logger = logging.getLogger("nexagrid.sandbox")


class ExecutionSandbox:
    """
    FAANG/Staff-Engineer Hardened Multi-Language Code Execution Engine.
    Features:
    1. Static AST / Pattern Security Analysis.
    2. Ephemeral Docker Micro-Container Isolation Engine (Zero Network, Read-Only Root, PIDs Limit, Cap Drop).
    3. POSIX resource limit fallback (CPU time, Memory, FDs, PIDs) if Docker unavailable.
    4. Async execution timeout enforcement.
    5. Clean temporary directory & container lifecycle management.
    """

    SUPPORTED_LANGUAGES = {
        "python": {"runner": "python3", "extension": ".py", "compile": False, "image": "python:3.11-slim"},
        "javascript": {"runner": "node", "extension": ".js", "compile": False, "image": "node:20-slim"},
        "go": {"runner": "go run", "extension": ".go", "compile": False, "image": "golang:1.22-alpine"},
        "rust": {"runner": "rustc", "extension": ".rs", "compile": True, "image": "rust:1.75-slim"},
        "java": {"runner": "javac", "extension": ".java", "compile": True, "image": "openjdk:21-slim"},
    }

    BLOCKED_PATTERNS = {
        "javascript": [
            "require('fs')", 'require("fs")', "require('child_process')",
            'require("child_process")', "process.exit", "eval(", "Function("
        ],
        "go": [
            "os/exec", "syscall", "unsafe"
        ],
        "rust": [
            "std::process::Command", "std::fs", "unsafe {", "raw_pointers"
        ],
        "java": [
            "Runtime.getRuntime()", "ProcessBuilder", "java.lang.reflect", "System.exit"
        ]
    }

    def __init__(self):
        self.docker_available = self._check_docker_availability()
        logger.info(f"ExecutionSandbox initialized. Docker container isolation available: {self.docker_available}")

    def _check_docker_availability(self) -> bool:
        """Check if Docker CLI or Docker daemon socket is available."""
        if shutil.which("docker") and (os.path.exists("/var/run/docker.sock") or os.access("/var/run/docker.sock", os.R_OK)):
            return True
        # Try running docker info fast
        try:
            res = os.system("docker info > /dev/null 2>&1")
            return res == 0
        except Exception:
            return False

    def _check_dangerous_code(self, code: str, language: str) -> Optional[str]:
        """Perform static AST inspection for Python & pattern matching for other languages."""
        if language == "python":
            try:
                tree = python_ast.parse(code)
                for node in python_ast.walk(tree):
                    if isinstance(node, python_ast.Import):
                        for alias in node.names:
                            if alias.name in ["os", "sys", "subprocess", "shutil", "socket", "ctypes", "pickle", "pty"]:
                                return f"Forbidden module import: '{alias.name}'"
                    elif isinstance(node, python_ast.ImportFrom):
                        if node.module in ["os", "sys", "subprocess", "shutil", "socket", "ctypes", "pickle", "pty"]:
                            return f"Forbidden module import: '{node.module}'"
                    elif isinstance(node, python_ast.Call):
                        if isinstance(node.func, python_ast.Name) and node.func.id in ["eval", "exec", "__import__", "open", "compile"]:
                            return f"Forbidden function call: '{node.func.id}()'"
            except SyntaxError:
                pass

        if language in self.BLOCKED_PATTERNS:
            for pattern in self.BLOCKED_PATTERNS[language]:
                if pattern in code:
                    return f"Forbidden pattern detected: '{pattern}'"

        return None

    def _set_posix_limits(self):
        """Set POSIX resource constraints for child process fallback sandbox."""
        # 1. CPU Time (5s max)
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        except Exception:
            pass

        # 2. Virtual Memory / Address Space (256MB max)
        try:
            mem_bytes = 256 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        except Exception:
            pass

        # 3. File Descriptors (64 max)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        except Exception:
            pass

        # 4. Process Count (16 max)
        try:
            resource.setrlimit(resource.RLIMIT_NPROC, (16, 16))
        except Exception:
            pass

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
                stderr=f"Language '{language}' is not supported. Supported: {list(self.SUPPORTED_LANGUAGES.keys())}",
                exit_code=-1,
                execution_time_ms=0,
                blocked=True
            )

        # 1. Static Security Analysis
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
            file_name = "Main.java" if language == "java" else f"main{lang_config['extension']}"
            code_file = Path(tmpdir) / file_name
            code_file.write_text(code, encoding="utf-8")

            stdin_bytes = stdin.encode("utf-8") if stdin else None

            # Route to Container Execution Driver if Docker is available
            if self.docker_available:
                result = await self._execute_container(tmpdir, file_name, language, lang_config, stdin_bytes, start_time)
            else:
                result = await self._execute_posix(tmpdir, file_name, language, lang_config, stdin_bytes, start_time)

            EXECUTION_DURATION.labels(language=language).observe(result.execution_time_ms / 1000.0)
            return result

    async def _execute_container(
        self,
        tmpdir: str,
        file_name: str,
        language: str,
        lang_config: Dict[str, Any],
        stdin_bytes: Optional[bytes],
        start_time: float
    ) -> ExecutionResult:
        """Execute code inside Docker micro-container with maximum security bounds."""
        container_name = f"nexagrid_sandbox_{hashlib.md5(f'{time.time()}_{file_name}'.encode()).hexdigest()[:10]}"
        image = lang_config["image"]

        # Formulate Docker isolation command
        docker_cmd = [
            "docker", "run", "--rm", "-i",
            "--name", container_name,
            "--net=none",
            "--memory=128m",
            "--cpus=0.5",
            "--pids-limit=32",
            "--read-only",
            "--tmpfs", "/tmp:exec,mode=1777,size=64m",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "-v", f"{tmpdir}:/app:ro",
            "-w", "/app",
            image
        ]

        if language == "python":
            docker_cmd.extend(["python3", file_name])
        elif language == "javascript":
            docker_cmd.extend(["node", file_name])
        elif language == "go":
            docker_cmd.extend(["go", "run", file_name])
        else:
            # Fallback for compiled inside container or POSIX driver
            return await self._execute_posix(tmpdir, file_name, language, lang_config, stdin_bytes, start_time)

        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=10.0
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return ExecutionResult(
                stdout=stdout_data.decode("utf-8", errors="replace"),
                stderr=stderr_data.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                execution_time_ms=elapsed_ms,
                blocked=False,
                metadata={"sandbox_driver": "docker_container", "image": image}
            )

        except asyncio.TimeoutError:
            # Kill running container
            os.system(f"docker kill {container_name} >/dev/null 2>&1")
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ExecutionResult(
                stdout="",
                stderr="Execution Error: Process exceeded maximum time limit (10.0 seconds).",
                exit_code=-1,
                execution_time_ms=elapsed_ms,
                blocked=True,
                metadata={"timeout": True, "sandbox_driver": "docker_container"}
            )
        except Exception as e:
            logger.warning(f"Docker execution error (falling back to POSIX): {e}")
            return await self._execute_posix(tmpdir, file_name, language, lang_config, stdin_bytes, start_time)

    async def _execute_posix(
        self,
        tmpdir: str,
        file_name: str,
        language: str,
        lang_config: Dict[str, Any],
        stdin_bytes: Optional[bytes],
        start_time: float
    ) -> ExecutionResult:
        """Execute code using tuned POSIX subprocess with resource limits."""
        code_file = Path(tmpdir) / file_name

        try:
            if language == "rust":
                binary_path = Path(tmpdir) / "main_bin"
                compile_proc = await asyncio.create_subprocess_exec(
                    "rustc", str(code_file), "-o", str(binary_path),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=tmpdir
                )
                c_stdout, c_stderr = await asyncio.wait_for(compile_proc.communicate(), timeout=10.0)
                if compile_proc.returncode != 0:
                    return ExecutionResult(
                        stdout="", stderr=c_stderr.decode("utf-8", errors="replace"),
                        exit_code=compile_proc.returncode or -1, execution_time_ms=0, blocked=False
                    )
                run_args = [str(binary_path)]

            elif language == "java":
                compile_proc = await asyncio.create_subprocess_exec(
                    "javac", str(code_file),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=tmpdir
                )
                c_stdout, c_stderr = await asyncio.wait_for(compile_proc.communicate(), timeout=10.0)
                if compile_proc.returncode != 0:
                    return ExecutionResult(
                        stdout="", stderr=c_stderr.decode("utf-8", errors="replace"),
                        exit_code=compile_proc.returncode or -1, execution_time_ms=0, blocked=False
                    )
                run_args = ["java", "-cp", tmpdir, "Main"]

            elif language == "go":
                run_args = ["go", "run", str(code_file)]
            elif language == "javascript":
                run_args = ["node", str(code_file)]
            else:
                run_args = ["python3", str(code_file)]

            proc = await asyncio.create_subprocess_exec(
                *run_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=self._set_posix_limits,
                cwd=tmpdir
            )

            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=10.0
            )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ExecutionResult(
                stdout=stdout_data.decode("utf-8", errors="replace"),
                stderr=stderr_data.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                execution_time_ms=elapsed_ms,
                blocked=False,
                metadata={"sandbox_driver": "posix_resource_limits"}
            )

        except asyncio.TimeoutError:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ExecutionResult(
                stdout="",
                stderr="Execution Error: Process exceeded maximum time limit (10.0 seconds).",
                exit_code=-1,
                execution_time_ms=elapsed_ms,
                blocked=True,
                metadata={"timeout": True, "sandbox_driver": "posix_resource_limits"}
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ExecutionResult(
                stdout="", stderr=f"System Execution Error: {str(e)}",
                exit_code=-1, execution_time_ms=elapsed_ms, blocked=True
            )


sandbox_engine = ExecutionSandbox()
sandbox_service = sandbox_engine
