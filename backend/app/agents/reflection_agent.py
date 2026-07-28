"""Reflection Agent module for evaluating retrieved context completeness and sufficiency.

The Reflection Agent evaluates retrieved evidence chunks against the user question
and the Planner Agent's goals to decide:
1. Is enough evidence available to answer the query accurately?
2. Are all requested entities/documents represented in the retrieved chunks?
3. What is the overall context coverage score (0.0 to 1.0)?
4. Is another retrieval round necessary?
5. What specific information is missing, and what follow-up queries should be executed?
"""

import json
import logging
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.agents.planner_agent import PlannerResult
from app.services.llm_service import generate_answer

logger = logging.getLogger(__name__)


class ReflectionResult(BaseModel):
    """Structured Pydantic result returned by the Reflection Agent."""

    is_sufficient: bool = Field(
        description="True if retrieved context contains sufficient evidence to answer the question"
    )
    documents_represented: bool = Field(
        description="True if all entities/documents specified in planner goals are present in chunks"
    )
    coverage_score: float = Field(
        default=0.0,
        description="Completeness score between 0.0 and 1.0 representing context coverage",
    )
    needs_another_retrieval: bool = Field(
        description="True if another retrieval round is required to fill context gaps"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="List of specific information gaps or unrepresented documents",
    )
    followup_queries: List[str] = Field(
        default_factory=list,
        description="Targeted follow-up search queries for the next retrieval iteration",
    )
    reasoning: str = Field(
        default="",
        description="Justification for sufficiency judgment and coverage calculation",
    )


_REFLECTION_SYSTEM_PROMPT = """\
You are an expert Retrieval Reflection Evaluator for a RAG system.
Your task is to critique retrieved context chunks and decide if they contain sufficient evidence to answer the user's question.

INPUT DATA:
- Question: "{question}"
- Question Category: {category}
- Target Entities/Documents: {entities}
- Information Needed: {info_needed}

RETRIEVED CHUNKS SUMMARY:
{chunk_summaries}

EVALUATION RULES:
1. COVERAGE SCORE: Calculate a float score between 0.0 and 1.0 measuring how well the retrieved chunks cover the question's target entities and information goals.
2. DOCUMENTS REPRESENTED: Set to true ONLY if all target entities/documents have relevant chunk representation.
3. IS SUFFICIENT: Set to true if the chunks provide strong, reliable evidence to answer the user comprehensively.
4. NEEDS ANOTHER RETRIEVAL: Set to true if coverage_score < 0.70 or key entities/information are missing AND targeted follow-up queries can retrieve them.
5. FOLLOW-UP QUERIES: If another retrieval is needed, generate 1 to 3 targeted, specific search queries to retrieve the missing information.
6. OUTPUT FORMAT: Output ONLY valid JSON matching this schema with no markdown code fence wrappers:

{{
  "is_sufficient": true,
  "documents_represented": true,
  "coverage_score": 0.91,
  "needs_another_retrieval": false,
  "missing_information": [],
  "followup_queries": [],
  "reasoning": "Both target documents contain sufficient thematic and plot evidence across retrieved chunks."
}}
"""


class ReflectionAgent:
    """Agent responsible for critiquing retrieved context quality and triggering second-turn retrieval."""

    @classmethod
    def evaluate(
        cls,
        question: str,
        planner_result: PlannerResult,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> ReflectionResult:
        """Evaluate retrieved chunks against question and planner goals.

        Args:
            question: User input query string.
            planner_result: PlannerResult containing categories, entities, and strategy.
            retrieved_chunks: List of chunk dictionaries retrieved so far.

        Returns:
            ReflectionResult evaluating coverage, document representation, and second-turn decisions.
        """
        if not retrieved_chunks:
            logger.info("ReflectionAgent: no chunks provided — returning zero coverage result.")
            return ReflectionResult(
                is_sufficient=False,
                documents_represented=False,
                coverage_score=0.0,
                needs_another_retrieval=True,
                missing_information=["No context chunks cleared similarity threshold"],
                followup_queries=planner_result.search_queries or [question],
                reasoning="Zero chunks retrieved during search pass.",
            )

        logger.info("ReflectionAgent: evaluating %d retrieved chunks...", len(retrieved_chunks))

        # Build concise summaries of chunks for prompt efficiency
        chunk_summaries = cls._build_chunk_summaries(retrieved_chunks)

        prompt = _REFLECTION_SYSTEM_PROMPT.format(
            question=question,
            category=planner_result.question_category,
            entities=json.dumps(planner_result.entities),
            info_needed=json.dumps(planner_result.information_needed),
            chunk_summaries=chunk_summaries,
        )

        try:
            raw_response = generate_answer(prompt)
            return cls._parse_response(raw_response, len(retrieved_chunks))
        except Exception as exc:
            logger.warning("ReflectionAgent LLM evaluation failed (%s). Using fallback logic.", exc)
            return cls._fallback_result(retrieved_chunks, exc)

    @classmethod
    def _build_chunk_summaries(cls, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into concise diagnostic summaries for the reflection prompt."""
        summaries = []
        for idx, chunk in enumerate(chunks[:12], start=1):
            doc = chunk.get("filename") or f"Doc #{chunk.get('document_id', '?')}"
            score = chunk.get("similarity_score", chunk.get("score", 0.0))
            text = chunk.get("chunk_text", "")
            snippet = text[:200].replace("\n", " ") + ("..." if len(text) > 200 else "")
            summaries.append(f"[{idx}] Source: {doc} | Score: {score:.3f}\nSnippet: {snippet}")

        return "\n\n".join(summaries) if summaries else "No snippet content available."

    @classmethod
    def _parse_response(cls, raw_output: str, total_chunks: int) -> ReflectionResult:
        """Parse raw LLM response into a ReflectionResult object."""
        if not raw_output or not isinstance(raw_output, str):
            return cls._fallback_result([], "Empty LLM reflection output")

        text = raw_output.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                cov_score = float(data.get("coverage_score", 0.8))
                cov_score = max(0.0, min(1.0, cov_score))

                is_suff = bool(data.get("is_sufficient", cov_score >= 0.70))
                docs_rep = bool(data.get("documents_represented", True))
                needs_2nd = bool(data.get("needs_another_retrieval", not is_suff))

                missing = [str(m).strip() for m in data.get("missing_information", []) if m and str(m).strip()]
                followups = [str(f).strip() for f in data.get("followup_queries", []) if f and str(f).strip()]
                reasoning = str(data.get("reasoning", "")).strip()

                return ReflectionResult(
                    is_sufficient=is_suff,
                    documents_represented=docs_rep,
                    coverage_score=cov_score,
                    needs_another_retrieval=needs_2nd,
                    missing_information=missing,
                    followup_queries=followups,
                    reasoning=reasoning,
                )
        except Exception as exc:
            logger.warning("ReflectionAgent JSON decode failed (%s) on output: %r", exc, text)

        return cls._fallback_result([], f"Parse error: {raw_output[:100]}")

    @classmethod
    def _fallback_result(cls, chunks: List[Dict[str, Any]], error: Any) -> ReflectionResult:
        """Fallback evaluation when reflection LLM service fails."""
        has_chunks = bool(chunks)
        return ReflectionResult(
            is_sufficient=has_chunks,
            documents_represented=has_chunks,
            coverage_score=0.75 if has_chunks else 0.0,
            needs_another_retrieval=False,
            missing_information=[],
            followup_queries=[],
            reasoning=f"Fallback reflection judgment applied ({error}). Chunks present: {has_chunks}",
        )
