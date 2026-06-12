"""Groq Provider — Groq API integration.

Fast inference fallback LLM provider.
Models: llama-3.1-8b-instant, llama-3.3-70b-versatile
"""

import logging
import os

from services.llm.provider import LLMProvider
from services.llm.errors import classify_error

logger = logging.getLogger(__name__)

# Groq model candidates in preference order
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class GroqProvider(LLMProvider):
    """Groq API provider."""

    def __init__(self):
        self._client = None
        self._models = GROQ_MODELS.copy()

    def _get_client(self):
        """Lazy-load the Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise RuntimeError("GROQ_API_KEY not set in environment")
                self._client = Groq(api_key=api_key)
            except ImportError:
                raise RuntimeError("groq package not installed. Run: pip install groq")
        return self._client

    def is_available(self) -> bool:
        """Check if Groq is available (API key is set)."""
        return bool(os.getenv("GROQ_API_KEY"))

    def get_name(self) -> str:
        return "groq"

    def get_models(self) -> list[str]:
        return self._models.copy()

    def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response using Groq API.

        Args:
            prompt: The input prompt
            model: Optional model name (defaults to llama-3.3-70b-versatile)

        Returns:
            Generated text response

        Raises:
            LLMError: On provider errors (classified)
        """
        client = self._get_client()
        model_name = model or self._models[0]

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that responds with valid JSON when asked."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise classify_error(e, "groq", model_name)
