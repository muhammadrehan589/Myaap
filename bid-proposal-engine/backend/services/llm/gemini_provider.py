"""Gemini Provider — Google Gemini API integration.

Primary LLM provider with multi-model fallback chain.
Models: gemini-2.0-flash, gemini-2.5-flash, gemini-2.0-flash-lite, gemini-2.5-flash-lite
"""

import logging
import os

from services.llm.provider import LLMProvider
from services.llm.errors import classify_error

logger = logging.getLogger(__name__)

# Gemini model candidates in preference order
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
]


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self):
        self._client = None
        self._models = GEMINI_MODELS.copy()

    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY not set in environment")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if Gemini is available (API key is set)."""
        return bool(os.getenv("GEMINI_API_KEY"))

    def get_name(self) -> str:
        return "gemini"

    def get_models(self) -> list[str]:
        return self._models.copy()

    def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response using Gemini API.

        Tries models in order if the specified model fails with retryable errors.

        Args:
            prompt: The input prompt
            model: Optional model name (defaults to first in list)

        Returns:
            Generated text response

        Raises:
            LLMError: On provider errors (classified)
        """
        client = self._get_client()
        models_to_try = [model] if model else self._models

        last_error = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text.strip()
            except Exception as e:
                last_error = e
                llm_error = classify_error(e, "gemini", model_name)
                logger.warning(f"Gemini model {model_name} failed: {llm_error}")

                # If not retryable, raise immediately
                if not llm_error.retryable:
                    raise llm_error

                # Continue to next model for retryable errors
                continue

        # All models exhausted
        raise classify_error(last_error, "gemini", models_to_try[-1] if models_to_try else None)
