"""Intent Router module for KnowledgeHub AI.

Classifies incoming user questions into either:
1. 'direct' pipeline: Fast single-pass retrieval for simple factual, definition, author, or page lookups.
2. 'agentic' pipeline: Full Planner -> Multi-Query Retriever -> Reflection Agent workflow for complex comparison, summarization, or cross-document analytical queries.

If confidence < 0.60, defaults safely to 'agentic'.
"""

import logging
import re
from typing import Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IntentResult(BaseModel):
    """Structured result returned by the Intent Router."""

    intent: str = Field(
        description="Query intent classification (e.g. factual_lookup, author_lookup, definition, page_lookup, comparison, summarization, analytical)"
    )
    confidence: float = Field(
        description="Router confidence score between 0.0 and 1.0"
    )
    pipeline: Literal["direct", "agentic"] = Field(
        description="Target execution pipeline: 'direct' or 'agentic'"
    )
    reasoning: str = Field(
        description="Brief rationale for the routing decision"
    )


class IntentRouter:
    """Enterprise router determining optimal retrieval execution path."""

    # Direct query heuristics (fast patterns)
    _DIRECT_PATTERNS = [
        (r"^\s*(who|what|where|when)\s+wrote\b", "author_lookup"),
        (r"^\s*who\s+is\s+the\s+author\b", "author_lookup"),
        (r"^\s*what\s+is\s+the\s+definition\b", "definition"),
        (r"^\s*define\b", "definition"),
        (r"^\s*which\s+page\b", "page_lookup"),
        (r"^\s*what\s+page\b", "page_lookup"),
        (r"^\s*what\s+is\b", "factual_lookup"),
        (r"^\s*who\s+is\b", "factual_lookup"),
    ]

    # Agentic query heuristics (complex patterns)
    _AGENTIC_PATTERNS = [
        (r"\bcompare\b", "comparison"),
        (r"\bcontrast\b", "comparison"),
        (r"\bdifference(s)?\b", "comparison"),
        (r"\bsummariz(e|ation)\b", "summarization"),
        (r"\boverview\b", "summarization"),
        (r"\banalyz(e|is)\b", "analytical"),
        (r"\bevaluat(e|ion)\b", "analytical"),
        (r"\bcontradict(ion|ory)?\b", "analytical"),
        (r"\b synthesiz(e|is)\b", "analytical"),
        (r"\bacross\s+(all|multiple|both|documents|books)\b", "analytical"),
    ]

    @classmethod
    def analyze(cls, question: str) -> IntentResult:
        """Analyze question intent and select 'direct' or 'agentic' pipeline.

        Args:
            question: Clean user query string.

        Returns:
            IntentResult with pipeline choice, confidence, intent category, and reasoning.
        """
        q_lower = question.strip().lower()

        # Step 1: Check Agentic patterns first (e.g. compare, summarize)
        for pattern, category in cls._AGENTIC_PATTERNS:
            if re.search(pattern, q_lower):
                logger.info("[IntentRouter] Matched Agentic pattern (%s): %r", category, question)
                return IntentResult(
                    intent=category,
                    confidence=0.92,
                    pipeline="agentic",
                    reasoning=f"Matched complex query keyword pattern '{category}'. Requires multi-query agentic synthesis.",
                )

        # Step 2: Check Direct patterns (e.g. who wrote, what page, who is author)
        for pattern, category in cls._DIRECT_PATTERNS:
            if re.search(pattern, q_lower):
                logger.info("[IntentRouter] Matched Direct pattern (%s): %r", category, question)
                return IntentResult(
                    intent=category,
                    confidence=0.90,
                    pipeline="direct",
                    reasoning=f"Matched direct lookup pattern '{category}'. Executing fast single-pass retrieval.",
                )

        # Step 3: Length & Complexity heuristics
        words = q_lower.split()
        if len(words) <= 7 and not any(w in q_lower for w in ["and", "or", "versus", "vs"]):
            logger.info("[IntentRouter] Short factual question heuristics: %r", question)
            return IntentResult(
                intent="factual_lookup",
                confidence=0.82,
                pipeline="direct",
                reasoning="Short factual query (<=7 words). Executing fast direct retrieval.",
            )

        # Step 4: Fallback - Complex or ambiguous queries default to Agentic
        logger.info("[IntentRouter] Defaulting to Agentic pipeline for multi-aspect query: %r", question)
        return IntentResult(
            intent="analytical",
            confidence=0.75,
            pipeline="agentic",
            reasoning="Open-ended or multi-aspect query. Defaulting to full Agentic pipeline for maximum answer quality.",
        )
