"""LLM Response Cache — In-memory cache with 24-hour TTL.

Caches LLM responses based on normalized prompt + provider + model.
Reduces API usage for repeated identical requests.

Cache key = hash(normalized_prompt + provider_name + model_name)
Cache TTL = 24 hours (configurable)

Thread-safe via simple locking (sufficient for single-process FastAPI).
"""

import hashlib
import json
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 24 * 60 * 60  # 24 hours


class ResponseCache:
    """In-memory LLM response cache with TTL expiration."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        """Initialize the cache.

        Args:
            ttl_seconds: Cache entry time-to-live in seconds (default: 24 hours)
        """
        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, prompt: str, provider: str, model: str) -> str:
        """Generate a cache key from prompt, provider, and model.

        Normalizes the prompt by stripping whitespace and lowercasing
        to improve cache hit rates for equivalent prompts.
        """
        normalized = prompt.strip().lower()
        raw = f"{normalized}|{provider}|{model}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, prompt: str, provider: str, model: str) -> Optional[str]:
        """Look up a cached response.

        Args:
            prompt: The input prompt
            provider: Provider name
            model: Model name

        Returns:
            Cached response text if found and not expired, None otherwise
        """
        key = self._make_key(prompt, provider, model)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            # Check expiration
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache expired for key {key[:12]}...")
                return None

            self._hits += 1
            logger.debug(f"Cache hit for key {key[:12]}...")
            return entry["response"]

    def set(self, prompt: str, provider: str, model: str, response: str) -> None:
        """Store a response in the cache.

        Args:
            prompt: The input prompt
            provider: Provider name
            model: Model name
            response: The LLM response text to cache
        """
        key = self._make_key(prompt, provider, model)

        with self._lock:
            self._cache[key] = {
                "response": response,
                "provider": provider,
                "model": model,
                "created_at": time.time(),
                "expires_at": time.time() + self._ttl,
            }
            logger.debug(f"Cached response for key {key[:12]}... (TTL: {self._ttl}s)")

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info(f"Cache cleared: {count} entries removed")
            return count

    def cleanup_expired(self) -> int:
        """Remove expired entries from the cache.

        Returns:
            Number of expired entries removed
        """
        now = time.time()
        removed = 0

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

        if removed > 0:
            logger.info(f"Cache cleanup: {removed} expired entries removed")
        return removed

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with size, hits, misses, hit_rate
        """
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total * 100, 1) if total > 0 else 0.0,
                "ttl_seconds": self._ttl,
            }
