"""LLM Service — Central orchestrator for LLM requests.

Handles:
- Provider fallback chain (Gemini → OpenAI → Groq)
- Retry logic with exponential backoff + jitter
- Response caching (24-hour TTL)
- Error classification and logging
- Guaranteed response (never crashes)

Usage:
    service = LLMService()
    response = service.generate(prompt)
"""

import logging
import random
import time
from typing import Optional

from services.llm.provider import LLMProvider
from services.llm.errors import LLMError, ErrorCategory
from services.llm.cache import ResponseCache
from services.llm.gemini_provider import GeminiProvider
from services.llm.openai_provider import OpenAIProvider
from services.llm.groq_provider import GroqProvider

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES_PER_PROVIDER = 3
BASE_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 16.0
JITTER_MAX_SECONDS = 0.5


class LLMService:
    """Central LLM service with fallback, retry, and caching.

    Provider order (configurable):
        1. Gemini (primary)
        2. OpenAI (fallback)
        3. Groq (fallback)

    Retry policy:
        - Max 3 retries per provider
        - Exponential backoff: 1s, 2s, 4s (+ jitter)
        - Only retries retryable errors (quota, rate_limit, timeout, server_error)
        - Non-retryable errors trigger immediate fallback

    Cache:
        - 24-hour TTL
        - Keyed on normalized prompt + provider + model
        - Returns cached response immediately on hit
    """

    def __init__(self, cache_ttl: int = 24 * 60 * 60):
        """Initialize the LLM service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 24 hours)
        """
        self._providers: list[LLMProvider] = []
        self._cache = ResponseCache(ttl_seconds=cache_ttl)
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "provider_attempts": {},
            "provider_failures": {},
        }

        # Register providers in fallback order
        self._register_providers()

    def _register_providers(self) -> None:
        """Register LLM providers in fallback order."""
        providers = [
            GeminiProvider(),
            OpenAIProvider(),
            GroqProvider(),
        ]

        for provider in providers:
            if provider.is_available():
                self._providers.append(provider)
                logger.info(f"Registered LLM provider: {provider.get_name()} ({', '.join(provider.get_models())})")
            else:
                logger.info(f"Skipped LLM provider: {provider.get_name()} (not configured)")

        if not self._providers:
            logger.warning("No LLM providers available! Set GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY")

    def _compute_backoff(self, attempt: int) -> float:
        """Compute exponential backoff delay with jitter.

        Args:
            attempt: Current retry attempt (0-based)

        Returns:
            Delay in seconds
        """
        delay = min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
        jitter = random.uniform(0, JITTER_MAX_SECONDS)
        return delay + jitter

    def generate(self, prompt: str, use_cache: bool = True) -> str:
        """Generate a response from an LLM with full fallback, retry, and caching.

        Args:
            prompt: The input prompt
            use_cache: Whether to use/response cache (default: True)

        Returns:
            The generated text response

        Raises:
            RuntimeError: If ALL providers fail after all retries
        """
        self._stats["total_requests"] += 1

        # Check cache first
        if use_cache:
            for provider in self._providers:
                for model in provider.get_models():
                    cached = self._cache.get(prompt, provider.get_name(), model)
                    if cached is not None:
                        self._stats["cache_hits"] += 1
                        logger.info(f"Cache hit: {provider.get_name()}/{model}")
                        return cached

        # Try each provider with retries
        last_error = None
        for provider in self._providers:
            try:
                response = self._generate_with_retry(provider, prompt)

                # Cache the successful response
                if use_cache:
                    model = provider.get_default_model()
                    self._cache.set(prompt, provider.get_name(), model, response)

                return response

            except LLMError as e:
                last_error = e
                logger.warning(f"Provider {provider.get_name()} failed: {e}")

                # Track failure stats
                name = provider.get_name()
                self._stats["provider_failures"][name] = self._stats["provider_failures"].get(name, 0) + 1

                # If fallback not allowed, raise immediately
                if not e.fallback:
                    raise RuntimeError(f"LLM provider {provider.get_name()} failed: {e}")

                # Continue to next provider
                continue

        # All providers exhausted
        raise RuntimeError(
            f"All LLM providers exhausted. Last error: {last_error}"
        )

    def _generate_with_retry(self, provider: LLMProvider, prompt: str) -> str:
        """Generate a response from a single provider with retry logic.

        Args:
            provider: The LLM provider to use
            prompt: The input prompt

        Returns:
            The generated text response

        Raises:
            LLMError: If all retries fail
        """
        name = provider.get_name()
        self._stats["provider_attempts"][name] = self._stats["provider_attempts"].get(name, 0) + 1

        last_error = None
        for attempt in range(MAX_RETRIES_PER_PROVIDER):
            try:
                response = provider.generate_response(prompt)
                if attempt > 0:
                    logger.info(f"Provider {name} succeeded on attempt {attempt + 1}")
                return response

            except LLMError as e:
                last_error = e

                # Non-retryable errors: fail immediately
                if not e.retryable:
                    logger.warning(f"Provider {name} non-retryable error: {e}")
                    raise e

                # Last attempt: fail
                if attempt == MAX_RETRIES_PER_PROVIDER - 1:
                    logger.warning(f"Provider {name} exhausted {MAX_RETRIES_PER_PROVIDER} retries")
                    raise e

                # Compute backoff and wait
                delay = self._compute_backoff(attempt)
                logger.info(f"Provider {name} retry {attempt + 1}/{MAX_RETRIES_PER_PROVIDER} in {delay:.1f}s (error: {e.category.value})")
                time.sleep(delay)

        # Should not reach here, but just in case
        raise last_error

    def get_stats(self) -> dict:
        """Get service statistics.

        Returns:
            Dict with request counts, cache stats, provider stats
        """
        return {
            "total_requests": self._stats["total_requests"],
            "cache_hits": self._stats["cache_hits"],
            "cache": self._cache.get_stats(),
            "providers_registered": [p.get_name() for p in self._providers],
            "provider_attempts": self._stats["provider_attempts"],
            "provider_failures": self._stats["provider_failures"],
        }

    def clear_cache(self) -> int:
        """Clear the response cache.

        Returns:
            Number of entries cleared
        """
        return self._cache.clear()

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names.

        Returns:
            List of provider name strings
        """
        return [p.get_name() for p in self._providers]
