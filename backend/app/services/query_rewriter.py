"""LLM-backed Query Rewriter service using Groq.

Transforms user questions into optimized, keyword-rich standalone search queries
before vector retrieval. Resolves pronouns and expands ambiguous phrases using
conversation history when available.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_REWRITE_PROMPT_TEMPLATE = """\
You are an expert search query optimization AI for a Retrieval-Augmented Generation (RAG) system.
Your task is to rewrite the user's input question into an expanded, keyword-rich search query optimized for vector database retrieval.

Guidelines:
1. PRESERVE INTENT: Maintain the core intent and informational need of the user.
2. EXPAND & ENRICH: Add relevant missing keywords, full book/author/topic names, and domain concepts to improve semantic search.
3. RESOLVE CONTEXT: If conversation history is provided, resolve ambiguous pronouns (e.g. "she", "he", "it", "they") or follow-up references using prior turns.
4. DO NOT ANSWER: Never answer or attempt to solve the question.
5. OUTPUT FORMAT: Output ONLY the raw rewritten query. Do NOT add markdown formatting, code fences, quote marks, labels, or explanatory text.
6. CLEAR QUESTIONS: If the question is already self-contained, clear, and keyword-rich, return it unchanged.

Examples:
Input: "When was she born?"
Output: Birth date of Ursula K. Le Guin

Input: "What does the author think about freedom?"
Output: Author's views on freedom and personal independence

Input: "Compare Omelas and Courage"
Output: Compare the themes, morality, happiness, freedom, and philosophy in The Ones Who Walk Away from Omelas and The Courage to Be Disliked

{history_section}

User Question: "{question}"
Rewritten Query:"""


def rewrite_query(question: str, history: Optional[list[dict]] = None) -> str:
    """Rewrite *question* using Groq into an optimized retrieval search query.

    Args:
        question: The original user question.
        history:  Optional list of prior turn dicts ``[{"role": ..., "content": ...}]``.

    Returns:
        The optimized search query string. Returns *question* unchanged if clear,
        or if Groq is unavailable/times out.
    """
    if not isinstance(question, str) or not question.strip():
        return question

    clean_question = question.strip()
    logger.info("Query Rewriter input: %r", clean_question)

    history_str = _format_history_context(history)
    prompt = _REWRITE_PROMPT_TEMPLATE.format(
        question=clean_question,
        history_section=history_str,
    )

    try:
        from app.services.llm_service import LLMServiceError, generate_answer
        raw_response = generate_answer(prompt)
    except Exception as exc:
        logger.warning("Query rewriter failed (%s). Falling back to original question.", exc)
        return clean_question

    rewritten = _clean_rewritten_output(raw_response, clean_question)
    
    if rewritten != clean_question:
        logger.info("Query Rewriter output: %r → %r", clean_question, rewritten)
    else:
        logger.info("Query Rewriter: question kept unchanged.")

    return rewritten


def _format_history_context(history: Optional[list[dict]]) -> str:
    """Format recent history messages into context text for the rewriter prompt."""
    if not history or not isinstance(history, list):
        return "Conversation History: None"

    recent = history[-6:] if len(history) > 6 else history
    lines = []
    for msg in recent:
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in {"user", "assistant"} and content:
                lines.append(f"{role.title()}: {content}")

    if not lines:
        return "Conversation History: None"

    return "Conversation History:\n" + "\n".join(lines)


def _clean_rewritten_output(raw_output: str, original_question: str) -> str:
    """Clean LLM output string, stripping fences, quotes, and prefixes."""
    if not raw_output or not isinstance(raw_output, str):
        return original_question

    text = raw_output.strip()

    # Strip markdown code blocks if added by LLM
    text = re.sub(r"^```(?:text|markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Strip surrounding quotes if wrapped
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()

    # Strip common unwanted prefixes
    text = re.sub(r"^(?:Rewritten Query|Optimized Query|Search Query):\s*", "", text, flags=re.IGNORECASE)
    text = text.strip()

    if not text:
        return original_question

    return text
