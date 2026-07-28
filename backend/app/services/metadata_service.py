"""AI-powered document metadata extraction using Groq.

Sends a structured prompt to Groq and parses the JSON response into a dict
with: title, author, summary, keywords, topics, language.

The function is intentionally fault-tolerant: if Groq is unavailable or
returns unparseable output the caller receives a dict of ``None`` values so
the upload pipeline can continue without interruption.
"""

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Maximum characters of document text sent to Groq.
# Keeps token usage low while still giving enough context for good metadata.
_TEXT_PREVIEW_CHARS = 4000

_METADATA_PROMPT_TEMPLATE = """\
You are a document metadata extractor. Read the following text and respond with ONLY a valid JSON object — no markdown fences, no explanation, no extra text.

Required JSON structure (use null for any field you cannot determine):
{{
  "title": "<document title or null>",
  "author": "<author name(s) or null>",
  "summary": "<2-3 sentence summary of the document>",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "topics": ["topic1", "topic2", "topic3"],
  "language": "<language name, e.g. English>"
}}

Document text:
{text}
"""


def generate_document_metadata(extracted_text: str) -> Dict[str, Any]:
    """Return AI-generated metadata for a document.

    Args:
        extracted_text: The full plain-text content extracted from a PDF.

    Returns:
        A dict with keys: title, author, summary, keywords, topics, language.
        Values are strings (or None on failure).  keywords and topics are
        returned as comma-separated strings so they can be stored in a plain
        TEXT column without a JSON dependency.
    """
    # Lazy import to avoid a circular dependency at module load time.
    from app.services.llm_service import LLMServiceError, generate_answer

    _empty: Dict[str, Any] = {
        "title": None,
        "author": None,
        "summary": None,
        "keywords": None,
        "topics": None,
        "language": None,
    }

    if not extracted_text or not extracted_text.strip():
        logger.warning("metadata_service: extracted_text is empty — skipping.")
        return _empty

    preview = extracted_text[:_TEXT_PREVIEW_CHARS].strip()
    prompt = _METADATA_PROMPT_TEMPLATE.format(text=preview)

    try:
        raw = generate_answer(prompt)
    except LLMServiceError as exc:
        logger.warning("metadata_service: Groq call failed (%s) — skipping metadata.", exc)
        return _empty

    # Groq sometimes wraps the JSON in markdown fences despite the instruction.
    # Strip them before parsing.
    cleaned = _strip_markdown_fences(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt a best-effort extraction of the JSON object.
        data = _extract_json_object(cleaned)

    if not isinstance(data, dict):
        logger.warning("metadata_service: could not parse JSON from Groq — skipping metadata.")
        return _empty

    # Normalise list fields to comma-separated strings.
    keywords_raw = data.get("keywords")
    topics_raw = data.get("topics")

    return {
        "title":    _str_or_none(data.get("title")),
        "author":   _str_or_none(data.get("author")),
        "summary":  _str_or_none(data.get("summary")),
        "keywords": _list_to_csv(keywords_raw),
        "topics":   _list_to_csv(topics_raw),
        "language": _str_or_none(data.get("language")),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json … ``` fences that Groq occasionally adds."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_object(text: str) -> Any:
    """Try to find the first {...} block in *text* and parse it."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _str_or_none(value: Any) -> Any:
    """Return the value as a stripped string, or None if blank / null."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s and s.lower() != "null" else None


def _list_to_csv(value: Any) -> Any:
    """Convert a list to a comma-separated string, or pass through strings."""
    if value is None:
        return None
    if isinstance(value, list):
        joined = ", ".join(str(v).strip() for v in value if v)
        return joined if joined else None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return None
