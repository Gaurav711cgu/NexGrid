import logging
from typing import Optional
from app.core.database import db

logger = logging.getLogger("nexagrid.ai_context")


class RAGContextService:
    """
    Retrieval-Augmented Generation (RAG) Context Builder for AI Pair Programming.
    Fetches historical execution telemetry and room document state to inject
    context into LLM prompts for accurate, room-aware code diagnostics.
    """

    async def build_context(self, room_id: Optional[str] = None) -> str:
        if not room_id:
            return "No historical room context available."

        try:
            # 1. Retrieve recent execution logs for room
            logs = await db.fetch(
                """
                SELECT language, stdout, stderr, exit_code, executed_at
                FROM execution_logs
                WHERE room_id = $1
                ORDER BY executed_at DESC
                LIMIT 3
                """,
                room_id,
            )

            if not logs:
                return "No prior execution history in this room."

            context_lines = ["Recent Execution History:"]
            for idx, log in enumerate(logs, 1):
                status = "SUCCESS" if log["exit_code"] == 0 else f"FAILED (Exit Code {log['exit_code']})"
                context_lines.append(
                    f"- Run #{idx} [{log['language']}]: {status}"
                )
                if log["stderr"]:
                    context_lines.append(f"  Stderr: {log['stderr'][:200]}")

            return "\n".join(context_lines)

        except Exception as e:
            logger.warning("Failed to build RAG context for room %s: %s", room_id, e)
            return "Execution history unavailable due to telemetry query timeout."


rag_context_service = RAGContextService()
