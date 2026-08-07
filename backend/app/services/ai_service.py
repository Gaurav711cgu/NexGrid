import asyncio
import logging
import httpx
import json
from typing import AsyncGenerator, Optional, Dict, Any
from app.core.config import settings
from app.services.circuit_breaker import ai_circuit_breaker
from app.core.metrics import AI_COMPLETION_DURATION, AI_TOKEN_USAGE
from app.prompts.registry import prompt_registry
from app.services.ai_context_service import rag_context_service
from app.services.ast_chunker import ast_chunker

logger = logging.getLogger("nexagrid.ai")


class AIService:
    """
    FAANG/Staff-Engineer Hardened Multi-Provider AI Engine.
    Features:
      - AST-Aware Code Context Parsing (ast_chunker)
      - Hybrid LLM Multi-Provider Router (Primary: Anthropic API, Secondary: Local/Self-Hosted LLM server)
      - Automatic API Failover on rate limits, errors, or circuit breaker trips
      - Token Usage & Estimated Cost ($ USD) Accounting
      - Prompt Version Governance & RAG Context Telemetry Integration
    """

    # Estimated costs per 1K tokens ($ USD) for tracking
    MODEL_COSTS = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "local-qwen-coder": {"input": 0.0, "output": 0.0},
    }

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client: %s", e)

        self.local_llm_url = getattr(settings, "LOCAL_LLM_URL", "http://localhost:11434/api/generate")

    async def stream_completion(
        self,
        action: str,
        code: str,
        language: str = "python",
        cursor_line: int = 0,
        context: Optional[str] = None,
        room_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:

        # 1. AST Code Context Enrichment
        ast_context_summary = ""
        if language.lower() == "python":
            chunks = ast_chunker.chunk_python_code(code)
            if chunks:
                ast_context_summary = f"\n[AST Structural Context: Found {len(chunks)} code units ({', '.join(c.name for c in chunks[:3])})]"

        # 2. RAG Context Injection
        rag_context = await rag_context_service.build_context(room_id=room_id)
        if context:
            rag_context += f"\nError Trace: {context}"
        if ast_context_summary:
            rag_context += ast_context_summary

        prompt = self._build_prompt(action, code, language, rag_context)

        # 3. Route Request via Primary Cloud Model vs Secondary Local LLM Failover
        if ai_circuit_breaker.allow_request() and self.client:
            try:
                async for token in self._stream_anthropic(action, prompt):
                    yield token
                return
            except Exception as e:
                logger.error(f"Primary Anthropic LLM Provider Error: {e}. Initiating Failover Router.")
                ai_circuit_breaker.record_failure()

        # 4. Secondary Provider: Local/Self-Hosted LLM Server (Ollama / vLLM API compatible)
        try:
            async for token in self._stream_local_llm(prompt):
                yield token
            return
        except Exception as e:
            logger.warning(f"Secondary Local LLM Provider unavailable ({e}). Using deterministic fallback assistant.")

        # 5. Fallback Assistant Engine
        async for token in self._generate_fallback(action, code, language, context):
            yield token

    async def _stream_anthropic(self, action: str, prompt: str) -> AsyncGenerator[str, None]:
        """Stream completion from Anthropic API with token accounting."""
        model = settings.AI_MODEL
        with AI_COMPLETION_DURATION.labels(model=model, action=action).time():
            stream = await self.client.messages.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            ai_circuit_breaker.record_success()

            async for chunk in stream:
                if chunk.type == "message_delta" and hasattr(chunk, "usage"):
                    if hasattr(chunk.usage, "output_tokens"):
                        AI_TOKEN_USAGE.labels(model=model, direction="output").inc(chunk.usage.output_tokens)

                if chunk.type == "message_start" and hasattr(chunk, "message"):
                    if hasattr(chunk.message, "usage") and hasattr(chunk.message.usage, "input_tokens"):
                        AI_TOKEN_USAGE.labels(model=model, direction="input").inc(chunk.message.usage.input_tokens)

                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                    yield chunk.delta.text

    async def _stream_local_llm(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream completion from Local LLM Server (Ollama / vLLM API compatible)."""
        AI_TOKEN_USAGE.labels(model="local-qwen-coder", direction="input").inc(len(prompt.split()))
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                self.local_llm_url,
                json={"model": "qwen2.5-coder", "prompt": prompt, "stream": False}
            )
            if res.status_code == 200:
                data = res.json()
                text = data.get("response", "")
                AI_TOKEN_USAGE.labels(model="local-qwen-coder", direction="output").inc(len(text.split()))
                yield text
            else:
                raise RuntimeError(f"Local LLM responded with HTTP {res.status_code}")

    def _build_prompt(self, action: str, code: str, language: str, rag_context: str) -> str:
        """Fetch prompt from PromptRegistry and format with context."""
        try:
            template = prompt_registry.get(action, version=settings.AI_PROMPT_VERSION)
            return template.format(
                language=language,
                code=code,
                rag_context=rag_context,
                room_id="default"
            )
        except Exception as e:
            logger.warning("Prompt registry lookup failed, using inline default: %s", e)
            return f"Language: {language}\nContext: {rag_context}\nCode:\n{code}"

    async def _generate_fallback(
        self,
        action: str,
        code: str,
        language: str,
        context: Optional[str]
    ) -> AsyncGenerator[str, None]:
        """Deterministic rule-based response generator when all AI providers are unavailable."""
        await asyncio.sleep(0.05)
        if action == "fix_error":
            yield f"```python\n# NexaGrid Rule-Based Diagnostic\n# Error Context: {context or 'None'}\n"
            yield "# Suggestion: Verify variable bindings and ensure valid exception handling.\n"
            yield f"{code}\n```"
        elif action == "explain":
            yield f"### Code Overview ({language.capitalize()})\n"
            yield f"The provided code consists of {len(code.splitlines())} lines.\n"
            yield "Key Logic: Executes linear instructions with standard error handling boundaries."
        else:
            yield f"# Completion fallback for {language}\n"
            yield f"{code}\n# End completion"


ai_service = AIService()
