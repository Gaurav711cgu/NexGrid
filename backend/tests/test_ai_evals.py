import pytest
import time
from app.services.vector_rag_service import vector_rag_service
from app.services.ai_service import ai_service


@pytest.mark.asyncio
async def test_vector_rag_indexing_and_retrieval():
    """Verify AST code chunk indexing and semantic vector retrieval."""
    sample_code = """
import math

def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert(self, val: int):
        pass

def solve_knapsack(weights, values, capacity):
    # Dynamic programming 0/1 knapsack solver
    dp = [0] * (capacity + 1)
    return dp[capacity]
"""
    # 1. Clear and Index the code
    vector_rag_service.clear()
    indexed_count = vector_rag_service.index_code("algorithms.py", sample_code)
    assert indexed_count >= 3

    # 2. Search query for Fibonacci
    start = time.perf_counter()
    results = vector_rag_service.search_relevant_chunks("fibonacci recursive function", top_k=2)
    latency_ms = (time.perf_counter() - start) * 1000

    # Ensure retrieval is sub-15ms
    assert latency_ms < 15.0
    assert len(results) > 0
    assert "fibonacci" in results[0]["name"].lower() or "calculate_fibonacci" in results[0]["code_snippet"]

    # 3. Search query for Knapsack
    knapsack_results = vector_rag_service.search_relevant_chunks("dynamic programming knapsack weights", top_k=1)
    assert len(knapsack_results) > 0
    assert "knapsack" in knapsack_results[0]["name"].lower()


@pytest.mark.asyncio
async def test_ai_stream_token_accounting_and_eval():
    """Verify AI completion produces valid tokens and tracks metrics."""
    tokens = []
    start_time = time.perf_counter()

    async for token in ai_service.stream_completion(
        action="explain",
        code="def add(a, b): return a + b",
        language="python"
    ):
        tokens.append(token)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    full_output = "".join(tokens)

    assert len(tokens) > 0
    assert len(full_output) > 0
    assert elapsed_ms < 2000.0  # Fast fallback or generation
