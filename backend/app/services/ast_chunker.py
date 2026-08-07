import ast
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

logger = logging.getLogger("nexagrid.ast_chunker")


@dataclass
class CodeChunk:
    """
    Represents a semantic chunk of code extracted via AST parsing.
    """
    chunk_type: str  # 'function', 'class', 'imports', 'global'
    name: str
    code_snippet: str
    start_line: int
    end_line: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ASTCodeChunker:
    """
    AST-Aware Code Chunking Engine for Python.
    Parses source code into semantic units (functions, classes, imports) to enable
    high-density RAG prompt context construction.
    """

    @staticmethod
    def chunk_python_code(code: str) -> List[CodeChunk]:
        """
        Parse Python source code using standard AST and extract semantic chunks.
        Falls back to line-based chunking if AST parsing fails (e.g. syntax error in draft code).
        """
        chunks: List[CodeChunk] = []
        lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except Exception as err:
            logger.warning(f"AST parsing failed for code chunker (falling back to plain text): {err}")
            # Fallback chunking by line blocks
            return [
                CodeChunk(
                    chunk_type="plain_text",
                    name="main",
                    code_snippet=code,
                    start_line=1,
                    end_line=len(lines)
                )
            ]

        # Extract top-level imports
        import_lines: List[str] = []
        import_start = None
        import_end = None

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if import_start is None:
                    import_start = node.lineno
                import_end = node.end_lineno or node.lineno
                snippet = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])
                import_lines.append(snippet)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = node.end_lineno or start
                snippet = "\n".join(lines[start - 1 : end])
                chunks.append(
                    CodeChunk(
                        chunk_type="function",
                        name=node.name,
                        code_snippet=snippet,
                        start_line=start,
                        end_line=end
                    )
                )
            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = node.end_lineno or start
                snippet = "\n".join(lines[start - 1 : end])
                chunks.append(
                    CodeChunk(
                        chunk_type="class",
                        name=node.name,
                        code_snippet=snippet,
                        start_line=start,
                        end_line=end
                    )
                )

        if import_lines and import_start is not None and import_end is not None:
            chunks.insert(
                0,
                CodeChunk(
                    chunk_type="imports",
                    name="imports",
                    code_snippet="\n".join(import_lines),
                    start_line=import_start,
                    end_line=import_end
                )
            )

        if not chunks:
            chunks.append(
                CodeChunk(
                    chunk_type="global",
                    name="script",
                    code_snippet=code,
                    start_line=1,
                    end_line=len(lines)
                )
            )

        return chunks


ast_chunker = ASTCodeChunker()
