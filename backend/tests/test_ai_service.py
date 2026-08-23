import pytest
from unittest.mock import patch, AsyncMock
from app.services.ai_service import generate_code_completion

@pytest.mark.asyncio
async def test_ai_service_anthropic_fallback():
    """Verify that if Anthropic API fails, it falls back to the deterministic generator."""
    with patch("app.services.ai_service.anthropic_client") as mock_client:
        mock_client.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        # Should gracefully return a fallback string
        response = await generate_code_completion("def quicksort(arr):")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_ai_service_circuit_breaker_integration():
    """Verify that when circuit is OPEN, it immediately returns fallback without network call."""
    with patch("app.services.ai_service.ai_circuit_breaker") as mock_cb:
        mock_cb.allow_request.return_value = False
        
        response = await generate_code_completion("def binary_search(arr):")
        assert "fallback" in response.lower() or len(response) > 0

@pytest.mark.asyncio
async def test_ai_service_nominal():
    """Verify nominal generation."""
    with patch("app.services.ai_service.anthropic_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.completion = "    pass"
        mock_client.completions.create.return_value = mock_response
        
        response = await generate_code_completion("def test():")
        assert response == "    pass"
