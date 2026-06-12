"""LLM Error Classification — Categorizes provider errors for retry/fallback decisions.

Every LLM error is classified into one of:
- quota_error: Provider quota exhausted (retry with backoff, then fallback)
- rate_limit_error: HTTP 429 (retry with backoff, then fallback)
- timeout_error: Request timed out (retry, then fallback)
- provider_failure: Server error 5xx (retry, then fallback)
- auth_error: Authentication failed (no retry, immediate fallback)
- invalid_request: Bad prompt/format (no retry, no fallback — raise immediately)
- unknown: Unclassified (retry once, then fallback)
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Classification of LLM provider errors."""
    QUOTA = "quota_error"
    RATE_LIMIT = "rate_limit_error"
    TIMEOUT = "timeout_error"
    PROVIDER_FAILURE = "provider_failure"
    AUTH = "auth_error"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"


# Whether each error category should be retried
RETRYABLE_CATEGORIES = {
    ErrorCategory.QUOTA: True,
    ErrorCategory.RATE_LIMIT: True,
    ErrorCategory.TIMEOUT: True,
    ErrorCategory.PROVIDER_FAILURE: True,
    ErrorCategory.AUTH: False,
    ErrorCategory.INVALID_REQUEST: False,
    ErrorCategory.UNKNOWN: True,
}

# Whether fallback should be attempted (vs raising immediately)
FALLBACK_CATEGORIES = {
    ErrorCategory.QUOTA: True,
    ErrorCategory.RATE_LIMIT: True,
    ErrorCategory.TIMEOUT: True,
    ErrorCategory.PROVIDER_FAILURE: True,
    ErrorCategory.AUTH: True,
    ErrorCategory.INVALID_REQUEST: False,
    ErrorCategory.UNKNOWN: True,
}


class LLMError(Exception):
    """Structured LLM error with classification."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        provider: str,
        model: str = None,
        original_error: Exception = None,
        retryable: bool = None,
    ):
        super().__init__(message)
        self.category = category
        self.provider = provider
        self.model = model
        self.original_error = original_error
        self.retryable = retryable if retryable is not None else RETRYABLE_CATEGORIES.get(category, True)
        self.fallback = FALLBACK_CATEGORIES.get(category, True)

    def __str__(self):
        model_str = f" (model: {self.model})" if self.model else ""
        return f"[{self.provider}{model_str}] {self.category.value}: {super().__str__()}"


def classify_error(error: Exception, provider: str, model: str = None) -> LLMError:
    """Classify an exception into an LLMError with proper category.

    Args:
        error: The original exception
        provider: Provider name (gemini, openai, groq)
        model: Model name if known

    Returns:
        LLMError with appropriate category and retryability
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Timeout errors
    if "timeout" in error_str or "timed out" in error_str or error_type in ("TimeoutError", "asyncio.TimeoutError"):
        return LLMError(
            message=str(error),
            category=ErrorCategory.TIMEOUT,
            provider=provider,
            model=model,
            original_error=error,
        )

    # Rate limit / quota errors
    if any(kw in error_str for kw in ["429", "rate limit", "rate_limit", "too many requests"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.RATE_LIMIT,
            provider=provider,
            model=model,
            original_error=error,
        )

    if any(kw in error_str for kw in ["quota", "resource_exhausted", "billing"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.QUOTA,
            provider=provider,
            model=model,
            original_error=error,
        )

    # Auth errors
    if any(kw in error_str for kw in ["401", "403", "forbidden", "unauthorized", "invalid api key", "authentication"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.AUTH,
            provider=provider,
            model=model,
            original_error=error,
        )

    # Server errors (5xx)
    if any(kw in error_str for kw in ["500", "502", "503", "504", "server error", "internal error", "overloaded", "unavailable"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.PROVIDER_FAILURE,
            provider=provider,
            model=model,
            original_error=error,
        )

    # Not found (model doesn't exist)
    if any(kw in error_str for kw in ["404", "not found", "model not found"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.AUTH,  # Treat as non-retryable for this model
            provider=provider,
            model=model,
            original_error=error,
        )

    # Invalid request
    if any(kw in error_str for kw in ["400", "bad request", "invalid", "malformed"]):
        return LLMError(
            message=str(error),
            category=ErrorCategory.INVALID_REQUEST,
            provider=provider,
            model=model,
            original_error=error,
        )

    # Unknown — default to retryable
    return LLMError(
        message=str(error),
        category=ErrorCategory.UNKNOWN,
        provider=provider,
        model=model,
        original_error=error,
    )
