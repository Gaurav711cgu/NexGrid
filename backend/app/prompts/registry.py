import os
import logging
from typing import Dict

logger = logging.getLogger("nexagrid.prompts")

PROMPTS_DIR = os.path.dirname(__file__)


class PromptRegistry:
    """
    Versioned Prompt Registry for ML Governance & Prompt Lifecycle Management.
    Loads versioned prompt templates from disk (app/prompts/<version>/<action>.txt).
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}

    def get(self, action: str, version: str = "v1") -> str:
        cache_key = f"{version}:{action}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        filepath = os.path.join(PROMPTS_DIR, version, f"{action}.txt")
        if not os.path.exists(filepath):
            logger.warning(
                "Prompt template %s not found at %s. Falling back to v1.",
                cache_key,
                filepath,
            )
            filepath = os.path.join(PROMPTS_DIR, "v1", f"{action}.txt")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No prompt template found for action '{action}'")

        with open(filepath, "r", encoding="utf-8") as f:
            template = f.read()

        self._cache[cache_key] = template
        return template


prompt_registry = PromptRegistry()
