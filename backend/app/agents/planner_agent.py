"""Planner Agent module for question analysis, classification, and retrieval strategy planning.

The Planner Agent analyzes incoming user questions to:
1. Classify questions into category types (factual, comparison, summarization, document_specific, analytical).
2. Extract document names, authors, and key entities.
3. Identify specific information types needed (e.g., themes, endings, characters, author perspectives).
4. Choose an optimal retrieval strategy (single, multi_document, comparison, iterative).
5. Generate focused search sub-queries to maximize retrieval precision and recall across targets.
6. Provide a confidence score (0.0 to 1.0) to allow graceful fallback to standard RAG if low.
"""

import json
import logging
import re
from typing import List

from pydantic import BaseModel, Field

from app.services.llm_service import generate_answer

logger = logging.getLogger(__name__)


class PlannerResult(BaseModel):
    """Structured Pydantic result returned by the Planner Agent."""

    question_category: str = Field(
        description="Category: factual | comparison | summarization | document_specific | analytical"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score between 0.0 and 1.0 (fall back to single retrieval if < 0.40)",
    )
    entities: List[str] = Field(
        default_factory=list,
        description="Extracted document names, book titles, author names, or key entities",
    )
    information_needed: List[str] = Field(
        default_factory=list,
        description="Specific information elements needed (e.g., themes, ending, author, characters)",
    )
    retrieval_strategy: str = Field(
        description="Retrieval strategy: single | multi_document | comparison | iterative"
    )
    search_queries: List[str] = Field(
        default_factory=list,
        description="Targeted search sub-queries for retrieval",
    )
    reasoning: str = Field(
        default="",
        description="Brief justification for the chosen strategy and sub-queries",
    )


_PLANNER_SYSTEM_PROMPT = """\
You are an expert AI Search Planner for an enterprise RAG system.
Your job is to analyze the user's question and plan an optimal retrieval strategy.

GUIDELINES:
1. QUESTION CATEGORY: Choose exactly one of: ["factual", "comparison", "summarization", "document_specific", "analytical"].
2. ENTITIES: Extract document names, book titles, authors, or key subjects present or implied in the question.
3. INFORMATION NEEDED: List specific aspects required (e.g., "themes", "ending", "author", "characters", "arguments", "methodology").
4. RETRIEVAL STRATEGY: Choose exactly one of: ["single", "multi_document", "comparison", "iterative"].
   - Use "comparison" when comparing 2 or more entities/documents. Generate separate focused sub-queries for EACH entity and aspect (e.g., "DocA themes", "DocA ending", "DocB themes", "DocB ending").
   - Use "multi_document" when multiple distinct sources or topics must be synthesized.
   - Use "iterative" for complex analytical questions needing multi-step retrieval.
   - Use "single" for straightforward factual or single-document questions.
5. CONFIDENCE SCORE: Return a float between 0.0 and 1.0 indicating your confidence in the question analysis and sub-query decomposition.
6. OUTPUT FORMAT: Output ONLY valid JSON matching this schema with no markdown wrapper outside:

{{
  "question_category": "comparison",
  "confidence": 0.95,
  "entities": ["The Ones Who Walk Away from Omelas", "Animal Farm"],
  "information_needed": ["themes", "ending"],
  "retrieval_strategy": "comparison",
  "search_queries": [
    "Omelas themes",
    "Omelas ending",
    "Animal Farm themes",
    "Animal Farm ending"
  ],
  "reasoning": "Comparison requires retrieving thematic and plot ending evidence from both documents separately."
}}

User Question: "{question}"
JSON Output:"""


class PlannerAgent:
    """Agent responsible for question decomposition, entity extraction, and retrieval strategy selection."""

    @classmethod
    def analyze(cls, question: str) -> PlannerResult:
        """Analyze user *question* and return a structured PlannerResult.

        Args:
            question: The user input query string.

        Returns:
            PlannerResult containing category, confidence, entities, information goals,
            retrieval strategy, targeted search queries, and reasoning.
        """
        if not isinstance(question, str) or not question.strip():
            return cls._fallback_result(question or "", reason="Empty question string provided")

        clean_question = question.strip()
        logger.info("PlannerAgent: analyzing question %r", clean_question)

        prompt = _PLANNER_SYSTEM_PROMPT.format(question=clean_question)

        try:
            raw_response = generate_answer(prompt)
            return cls._parse_response(raw_response, clean_question)
        except Exception as exc:
            logger.warning("PlannerAgent failed LLM call or parse (%s). Returning fallback.", exc)
            return cls._fallback_result(clean_question, reason=f"LLM execution error: {exc}")

    @classmethod
    def _parse_response(cls, raw_output: str, original_question: str) -> PlannerResult:
        """Clean and parse LLM response into a validated PlannerResult Pydantic object."""
        if not raw_output or not isinstance(raw_output, str):
            return cls._fallback_result(original_question, reason="Empty LLM output")

        text = raw_output.strip()
        # Clean markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # Normalize values
                category = str(data.get("question_category", "factual")).lower()
                if category not in {"factual", "comparison", "summarization", "document_specific", "analytical"}:
                    category = "factual"

                strategy = str(data.get("retrieval_strategy", "single")).lower()
                if strategy not in {"single", "multi_document", "comparison", "iterative"}:
                    strategy = "single"

                confidence = float(data.get("confidence", 0.9))
                confidence = max(0.0, min(1.0, confidence))

                entities = [str(e).strip() for e in data.get("entities", []) if e and str(e).strip()]
                info_needed = [str(i).strip() for i in data.get("information_needed", []) if i and str(i).strip()]
                queries = [str(q).strip() for q in data.get("search_queries", []) if q and str(q).strip()]

                if not queries:
                    queries = [original_question]

                reasoning = str(data.get("reasoning", "")).strip()

                return PlannerResult(
                    question_category=category,
                    confidence=confidence,
                    entities=entities,
                    information_needed=info_needed,
                    retrieval_strategy=strategy,
                    search_queries=queries,
                    reasoning=reasoning,
                )
        except Exception as exc:
            logger.warning("PlannerAgent JSON decode failed (%s) on output: %r", exc, text)

        return cls._fallback_result(original_question, reason="Failed to parse JSON response")

    @classmethod
    def _fallback_result(cls, question: str, reason: str) -> PlannerResult:
        """Safe fallback result with confidence below 0.40 to trigger single-shot fallback."""
        return PlannerResult(
            question_category="factual",
            confidence=0.35,
            entities=[],
            information_needed=[],
            retrieval_strategy="single",
            search_queries=[question] if question else [],
            reasoning=f"Fallback planner configuration triggered: {reason}",
        )
