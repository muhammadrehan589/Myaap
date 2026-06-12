"""OpenAI Provider — OpenAI API integration.

Fallback LLM provider when Gemini is unavailable.
Models: gpt-4o-mini, gpt-3.5-turbo
"""

import logging
import os

from services.llm.provider import LLMProvider
from services.llm.errors import classify_error

logger = logging.getLogger(__name__)

# OpenAI model candidates in preference order
OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-3.5-turbo",
]


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self):
        self._client = None
        self._models = OPENAI_MODELS.copy()

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise RuntimeError("OPENAI_API_KEY not set in environment")
                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI is available (API key is set)."""
        return bool(os.getenv("OPENAI_API_KEY"))

    def get_name(self) -> str:
        return "openai"

    def get_models(self) -> list[str]:
        return self._models.copy()

    def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response using OpenAI API.

        Args:
            prompt: The input prompt
            model: Optional model name (defaults to gpt-4o-mini)

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
            raise classify_error(e, "openai", model_name)
