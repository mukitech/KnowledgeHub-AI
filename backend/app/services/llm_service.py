"""Groq-backed answer generation for the RAG pipeline."""

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from groq import APIError, APITimeoutError, Groq

logger = logging.getLogger(__name__)
_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_REQUEST_TIMEOUT_SECONDS = 30.0


class LLMServiceError(RuntimeError):
    """Raised when the configured LLM provider cannot return an answer."""


class LLMConfigurationError(LLMServiceError):
    """Raised when the server cannot authenticate with the LLM provider."""


class LLMTimeoutError(LLMServiceError):
    """Raised when the LLM request exceeds its configured timeout."""


@lru_cache(maxsize=1)
def _get_groq_client() -> Groq:
    """Create and cache one Groq client for the lifetime of the process."""
    load_dotenv(_ENV_PATH)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMConfigurationError("GROQ_API_KEY is not configured")

    return Groq(api_key=api_key, timeout=_REQUEST_TIMEOUT_SECONDS)


def generate_answer(prompt: str) -> str:
    """Send a prepared RAG prompt to Groq and return only the answer text."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise LLMServiceError("Prompt cannot be empty")

    try:
        completion = _get_groq_client().chat.completions.create(
            model=os.getenv("LLM_MODEL", _DEFAULT_MODEL),
            messages=[{"role": "user", "content": prompt}],
        )
    except LLMServiceError:
        raise
    except APITimeoutError as exc:
        logger.warning("Groq request timed out")
        raise LLMTimeoutError("Groq request timed out") from exc
    except APIError as exc:
        logger.exception("Groq API request failed")
        raise LLMServiceError("Groq could not generate an answer") from exc
    except Exception as exc:
        logger.exception("Unexpected Groq request failure")
        raise LLMServiceError("Groq could not generate an answer") from exc

    choices = getattr(completion, "choices", None)
    answer = choices[0].message.content if choices else None
    if not isinstance(answer, str) or not answer.strip():
        raise LLMServiceError("Groq returned an empty response")

    return answer.strip()
