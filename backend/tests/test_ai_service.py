import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.ai_service import ai_service
from app.services.circuit_breaker import ai_circuit_breaker

@pytest.mark.asyncio
async def test_ai_service_anthropic_fallback():
    """Verify that if Anthropic API fails, it falls back to the deterministic generator."""
    with patch.object(ai_service, "_stream_anthropic", side_effect=Exception("API Error")):
        with patch.object(ai_service, "_stream_local_llm", side_effect=Exception("Local LLM Error")):
            # Should gracefully return a fallback string
            response_chunks = [chunk async for chunk in ai_service.stream_completion("explain", "def quicksort(arr):")]
            response = "".join(response_chunks)
            assert response is not None
            assert len(response) > 0
            assert "Code Overview" in response

@pytest.mark.asyncio
async def test_ai_service_circuit_breaker_integration():
    """Verify that when circuit is OPEN, it skips Anthropic call."""
    with patch.object(ai_circuit_breaker, "allow_request", return_value=False):
        with patch.object(ai_service, "_stream_local_llm", side_effect=Exception("Local LLM Error")):
            response_chunks = [chunk async for chunk in ai_service.stream_completion("explain", "def binary_search(arr):")]
            response = "".join(response_chunks)
            assert len(response) > 0

@pytest.mark.asyncio
async def test_ai_service_nominal():
    """Verify nominal generation."""
    
    async def mock_stream_anthropic(*args, **kwargs):
        yield "    pass"

    with patch.object(ai_service, "client", new=MagicMock()):
        with patch.object(ai_service, "_stream_anthropic", side_effect=mock_stream_anthropic):
            response_chunks = [chunk async for chunk in ai_service.stream_completion("fix_error", "def test():")]
            response = "".join(response_chunks)
            assert response == "    pass"
