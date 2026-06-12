"""LLM Service — Production-ready multi-provider architecture.

Provides:
- Abstract LLMProvider interface
- Concrete providers: Gemini, OpenAI, Groq
- Central LLMService with fallback, retry, caching
- Error classification and handling
"""

from services.llm.provider import LLMProvider
from services.llm.errors import LLMError, ErrorCategory
from services.llm.cache import ResponseCache
from services.llm.service import LLMService

__all__ = [
    "LLMProvider",
    "LLMError",
    "ErrorCategory",
    "ResponseCache",
    "LLMService",
]
