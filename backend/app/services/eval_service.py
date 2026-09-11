import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class EvalResult:
    test_name: str
    passed: bool
    latency_ms: float
    groundedness_score: float
    lexical_similarity: float
    token_count: int
    details: Dict[str, Any]


class LLMEvalService:
    """
    Production LLM Evaluation Framework for Code Generation & Analysis.
    Evaluates:
      - Groundedness (context entailment)
      - Lexical Similarity (n-gram / token overlap)
      - Performance Regressions (latency & token budget)
    """

    @staticmethod
    def calculate_lexical_similarity(reference: str, hypothesis: str) -> float:
        """Compute token-level Jaccard similarity between reference and hypothesis."""
        ref_tokens = set(reference.lower().split())
        hyp_tokens = set(hypothesis.lower().split())
        if not ref_tokens or not hyp_tokens:
            return 0.0
        intersection = ref_tokens.intersection(hyp_tokens)
        union = ref_tokens.union(hyp_tokens)
        return len(intersection) / len(union)

    @staticmethod
    def calculate_groundedness(response: str, context: str) -> float:
        """
        Evaluate whether the generated response is grounded in the provided code/context.
        Checks keyword coverage of symbols, errors, and type names.
        """
        context_words = set([w for w in context.lower().replace(":", " ").replace("(", " ").split() if len(w) > 3])
        response_words = set(response.lower().split())
        if not context_words:
            return 1.0

        overlap = context_words.intersection(response_words)
        return min(1.0, len(overlap) / (min(len(context_words), 10)))

    @classmethod
    def evaluate_response(
        cls,
        test_name: str,
        response: str,
        context: str,
        reference: Optional[str] = None,
        latency_ms: float = 0.0,
        max_latency_threshold_ms: float = 3000.0,
        min_groundedness_threshold: float = 0.2
    ) -> EvalResult:
        """Run complete evaluation metrics on a single LLM response."""
        groundedness = cls.calculate_groundedness(response, context)
        similarity = cls.calculate_lexical_similarity(reference, response) if reference else 1.0
        token_count = len(response.split())

        passed = (
            groundedness >= min_groundedness_threshold and
            latency_ms <= max_latency_threshold_ms and
            len(response.strip()) > 0
        )

        return EvalResult(
            test_name=test_name,
            passed=passed,
            latency_ms=round(latency_ms, 2),
            groundedness_score=round(groundedness, 4),
            lexical_similarity=round(similarity, 4),
            token_count=token_count,
            details={
                "within_latency_budget": latency_ms <= max_latency_threshold_ms,
                "grounded": groundedness >= min_groundedness_threshold
            }
        )


eval_service = LLMEvalService()
