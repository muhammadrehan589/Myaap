"""LLM Provider — Abstract base class for all LLM providers.

Every provider must implement:
- generate_response(prompt) -> str
- is_available() -> bool
- get_name() -> str
- get_models() -> list[str]

Providers handle a single model each. The LLMService orchestrates
multiple providers with fallback and retry logic.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt
            model: Optional model override (uses default if None)

        Returns:
            The generated text response

        Raises:
            LLMError: On any provider error (classified by errors.classify_error)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is currently available.

        Returns:
            True if the provider can accept requests, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the provider name.

        Returns:
            Provider name string (e.g., 'gemini', 'openai', 'groq')
        """
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        """Get the list of available models for this provider.

        Returns:
            List of model name strings, ordered by preference
        """
        pass

    def get_default_model(self) -> str:
        """Get the default (first) model for this provider.

        Returns:
            The first model in the list, or None if no models
        """
        models = self.get_models()
        return models[0] if models else None
