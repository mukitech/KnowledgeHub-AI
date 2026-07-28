"""Planner Service wrapper module for backward compatibility.

Wraps the new Agentic `PlannerAgent` to ensure existing callers of `generate_search_queries`
continue working seamlessly without breaking changes.
"""

import logging
from typing import List

from app.agents.planner_agent import PlannerAgent

logger = logging.getLogger(__name__)


def generate_search_queries(question: str) -> List[str]:
    """Decompose *question* into distinct search queries using PlannerAgent.

    Args:
        question: The user's input query or question.

    Returns:
        List of search query strings. Returns ``[question]`` as a fallback if empty or failed.
    """
    if not isinstance(question, str) or not question.strip():
        return [question] if isinstance(question, str) and question else []

    clean_question = question.strip()
    logger.info("planner_service wrapper: delegating query generation to PlannerAgent for %r", clean_question)

    try:
        result = PlannerAgent.analyze(clean_question)
        if result and result.search_queries:
            return result.search_queries
    except Exception as exc:
        logger.warning("planner_service wrapper: PlannerAgent failed (%s). Falling back to original question.", exc)

    return [clean_question]
