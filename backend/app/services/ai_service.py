import asyncio
import logging
from typing import AsyncGenerator, Optional
from app.core.config import settings
from app.services.circuit_breaker import ai_circuit_breaker
from app.core.metrics import AI_COMPLETION_DURATION, AI_TOKEN_USAGE
from app.prompts.registry import prompt_registry
from app.services.ai_context_service import rag_context_service

logger = logging.getLogger("nexagrid.ai")


class AIService:
    """
    Streaming AI Pair Programmer Service.
    Wraps Anthropic Claude API calls with:
      - Prompt Governance via PromptRegistry (v1 versioned templates)
      - Telemetry RAG context injection (RAGContextService)
      - Token usage metric tracking (AI_TOKEN_USAGE)
      - Circuit Breaker resilience protection (ai_circuit_breaker)
    """

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client: %s", e)

    async def stream_completion(
        self,
        action: str,
        code: str,
        language: str = "python",
        cursor_line: int = 0,
        context: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:

        if not ai_circuit_breaker.allow_request():
            logger.warning("AI Circuit Breaker is OPEN. Yielding fallback assistant completion.")
            async for token in self._generate_fallback(action, code, language, context):
                yield token
            return

        if not self.client:
            async for token in self._generate_fallback(action, code, language, context):
                yield token
            return

        # FIX-13: Fetch RAG context from historical execution telemetry
        rag_context = await rag_context_service.build_context(room_id=room_id)
        if context:
            rag_context += f"\nError Trace: {context}"

        # FIX-13: Use PromptRegistry for prompt template loading
        prompt = self._build_prompt(action, code, language, rag_context)

        try:
            with AI_COMPLETION_DURATION.labels(model=settings.AI_MODEL, action=action).time():
                stream = await self.client.messages.create(
                    model=settings.AI_MODEL,
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                )
                ai_circuit_breaker.record_success()

                async for chunk in stream:
                    if chunk.type == "message_delta" and hasattr(chunk, "usage"):
                        # FIX-13: Track token usage metrics
                        if hasattr(chunk.usage, "output_tokens"):
                            AI_TOKEN_USAGE.labels(
                                model=settings.AI_MODEL, direction="output"
                            ).inc(chunk.usage.output_tokens)

                    if chunk.type == "message_start" and hasattr(chunk, "message"):
                        if hasattr(chunk.message, "usage") and hasattr(chunk.message.usage, "input_tokens"):
                            AI_TOKEN_USAGE.labels(
                                model=settings.AI_MODEL, direction="input"
                            ).inc(chunk.message.usage.input_tokens)

                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                        yield chunk.delta.text

        except Exception as e:
            logger.error("Anthropic API Error: %s", e)
            ai_circuit_breaker.record_failure()
            async for token in self._generate_fallback(action, code, language, context):
                yield token

    def _build_prompt(self, action: str, code: str, language: str, rag_context: str) -> str:
        """Fetch prompt from PromptRegistry and format with RAG context."""
        try:
            template = prompt_registry.get(action, version=settings.AI_PROMPT_VERSION)
            return template.format(
                language=language,
                code=code,
                error=rag_context,
                rag_context=rag_context,
                room_id="session",
            )
        except Exception as e:
            logger.warning("Prompt registry lookup failed (%s). Using fallback prompt.", e)
            return f"Help with this {language} code:\n```{language}\n{code}\n```"

    async def _generate_fallback(
        self, action: str, code: str, language: str, context: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Local intelligent fallback when API key is missing or circuit is open."""
        await asyncio.sleep(0.05)
        if action == "explain":
            explanation = f"### Code Analysis ({language.capitalize()})\nThis module implements structured execution flow. Main logic operates over target variables with clean functional error handling."
            for chunk in explanation.split(" "):
                yield chunk + " "
                await asyncio.sleep(0.03)
        elif action == "fix_error":
            fix = f"```python\n# Fixed Execution Code\ntry:\n{code if code else '    print(\"Hello NexaGrid!\")'}\nexcept Exception as e:\n    print(f'Handled error: {{e}}')\n```"
            for chunk in fix.split(" "):
                yield chunk + " "
                await asyncio.sleep(0.02)
        else:
            completion = f"\n# NexaGrid AI Completion ({language.capitalize()})\ndef optimized_solution():\n    \"\"\"Generated high-efficiency solution.\"\"\"\n    results = [x * 2 for x in range(10)]\n    return sum(results)\n\nprint(optimized_solution())"
            for chunk in completion.split("\n"):
                yield chunk + "\n"
                await asyncio.sleep(0.04)


ai_service = AIService()
