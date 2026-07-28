"""Retrieval Controller module orchestrating the Production-Optimized RAG Pipeline.

Orchestration Architecture:
                       User Question
                             │
                             ▼
                     Query Rewriter
                             │
                             ▼
                      Intent Router
                   ┌─────────┴─────────┐
                   │                   │
              Direct Pipeline     Agentic Pipeline
                   │          Planner → Retrieval → Reflection
                   └─────────┬─────────┘
                             ▼
                      Semantic Cache
                             │
                      Cache Hit? ─────────► Return Cached Answer (<100ms)
                             │
                            No
                             ▼
                      Prompt Builder
                             ▼
                        Groq LLM
                             ▼
                     Store in Cache
                             │
                             ▼
                          Response

Cost & Scale Limits:
- Max Planner search sub-queries = 5
- Max Reflection follow-up queries = 2
- Max Retrieval iterations = 2
- Max total chunks = 10 (Dynamic top_k: Direct=3..5, Comparison=8, Analytical=10)
"""

import logging
import time
from typing import Any, Dict, List, Tuple

from app.agents.intent_router import IntentResult, IntentRouter
from app.agents.planner_agent import PlannerAgent, PlannerResult
from app.agents.reflection_agent import ReflectionAgent, ReflectionResult
from app.services.llm_service import generate_answer
from app.services.memory_service import add_assistant_message, add_user_message, get_history
from app.services.query_rewriter import rewrite_query
from app.services.retriever import retrieve_relevant_chunks
from app.services.semantic_cache import SemanticCache
from app.utils.prompt_builder import build_rag_prompt

logger = logging.getLogger(__name__)

# Configurable Production Limits
_MAX_PLANNER_QUERIES = 5
_MAX_REFLECTION_QUERIES = 2
_MAX_ITERATIONS = 2
_MAX_CHUNKS_CAP = 10
_NO_RELEVANT_CHUNKS_MESSAGE = "I couldn't find relevant information in the uploaded documents."


class RetrievalController:
    """Orchestrator for the Production-Optimized Agentic RAG pipeline."""

    @classmethod
    def process_chat_request(cls, session_id: str, question: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Execute production-optimized RAG workflow for a given chat session and question.

        Args:
            session_id: Conversation session identifier.
            question: Clean user query string.

        Returns:
            Tuple of (answer_text, final_retrieved_chunks).
        """
        start_total = time.perf_counter()
        kb_version = SemanticCache.get_kb_version()

        logger.info("==================================================")
        logger.info("RAG PIPELINE STARTED | Session: %s | KB: %s", session_id, kb_version)
        logger.info("User Question: %r", question)
        logger.info("==================================================")

        # Step 1: Conversation History & Query Rewriting
        t0 = time.perf_counter()
        history = get_history(session_id)
        retrieval_query = rewrite_query(question, history)
        t_rewrite = (time.perf_counter() - t0) * 1000.0

        if retrieval_query != question:
            logger.info("[Step 1] Query Rewritten: %r -> %r (%.1f ms)", question, retrieval_query, t_rewrite)
        else:
            logger.info("[Step 1] Query kept unchanged: %r (%.1f ms)", retrieval_query, t_rewrite)

        # Step 2: Intent Router
        t0 = time.perf_counter()
        intent_result: IntentResult = IntentRouter.analyze(retrieval_query)
        t_router = (time.perf_counter() - t0) * 1000.0
        cls._log_intent_result(intent_result, t_router)

        # Step 3: Semantic Cache Lookup
        t0 = time.perf_counter()
        cached_match = SemanticCache.get(
            question=retrieval_query,
            session_id=session_id,
            kb_version=kb_version,
            threshold=0.95,
        )
        t_cache = (time.perf_counter() - t0) * 1000.0

        if cached_match:
            t_total = time.perf_counter() - start_total
            cls._log_cache_hit(intent_result, t_total)
            add_user_message(session_id, question)
            add_assistant_message(session_id, cached_match.answer)
            return cached_match.answer, cached_match.citations

        logger.info("[Step 3] Semantic Cache MISS (%.1f ms) — Proceeding to %s Pipeline", t_cache, intent_result.pipeline.upper())

        # Step 4: Execute Selected Pipeline (Direct vs Agentic)
        final_chunks: List[Dict[str, Any]] = []
        all_retrieved_batches: List[List[Dict[str, Any]]] = []

        t_planner_ms = 0.0
        t_retriever_ms = 0.0
        t_reflection_ms = 0.0
        second_retrieval_used = "No"

        if intent_result.pipeline == "direct":
            # --- DIRECT PIPELINE ---
            # Determine dynamic top_k (3 for factual, 5 for definitions/pages)
            target_top_k = 3 if intent_result.intent in ("factual_lookup", "author_lookup") else 5
            logger.info("[Direct Pipeline] Executing single-pass retrieval with top_k=%d...", target_top_k)

            t0 = time.perf_counter()
            try:
                direct_batch = retrieve_relevant_chunks(retrieval_query, top_k=target_top_k)
                if direct_batch:
                    all_retrieved_batches.append(direct_batch)
            except Exception as exc:
                logger.error("[Direct Pipeline] Single retrieval failed: %s", exc)

            t_retriever_ms = (time.perf_counter() - t0) * 1000.0
            final_chunks = cls._merge_deduplicate_rerank(all_retrieved_batches, top_k=target_top_k)

        else:
            # --- AGENTIC PIPELINE ---
            # Dynamic top_k for Agentic pipeline
            if intent_result.intent == "comparison":
                target_top_k = 8
            elif intent_result.intent in ("summarization", "analytical"):
                target_top_k = 10
            else:
                target_top_k = 10

            # Step A: Planner Agent
            t0 = time.perf_counter()
            planner_result: PlannerResult = PlannerAgent.analyze(retrieval_query)
            t_planner_ms = (time.perf_counter() - t0) * 1000.0
            cls._log_planner_result(planner_result)

            # Enforce Cost Limit: Max 5 planner search queries
            search_queries = (planner_result.search_queries or [retrieval_query])[:_MAX_PLANNER_QUERIES]

            # Step B: Iteration 1 Retrieval
            t0 = time.perf_counter()
            logger.info("--- RETRIEVAL ITERATION 1 ---")
            logger.info("Executing %d sub-queries: %r", len(search_queries), search_queries)

            for sq in search_queries:
                try:
                    batch = retrieve_relevant_chunks(sq, top_k=5)
                    if batch:
                        all_retrieved_batches.append(batch)
                except Exception as exc:
                    logger.warning("Retrieval failed for sub-query %r (%s).", sq, exc)

            merged_iter1_chunks = cls._merge_deduplicate_rerank(all_retrieved_batches, top_k=target_top_k)
            t_retriever_ms += (time.perf_counter() - t0) * 1000.0

            # Step C: Reflection Agent
            t0 = time.perf_counter()
            reflection_result: ReflectionResult = ReflectionAgent.evaluate(
                question=retrieval_query,
                planner_result=planner_result,
                retrieved_chunks=merged_iter1_chunks,
            )
            t_reflection_ms += (time.perf_counter() - t0) * 1000.0
            cls._log_reflection_result(reflection_result, iteration=1, chunk_count=len(merged_iter1_chunks))

            # Step D: Optional Iteration 2
            if (
                reflection_result.needs_another_retrieval
                and reflection_result.followup_queries
            ):
                second_retrieval_used = "Yes"
                followup_queries = reflection_result.followup_queries[:_MAX_REFLECTION_QUERIES]
                logger.info("--- RETRIEVAL ITERATION 2 (Triggered by Reflection Agent) ---")
                logger.info("Executing %d follow-up queries: %r", len(followup_queries), followup_queries)

                t0 = time.perf_counter()
                for fq in followup_queries:
                    try:
                        batch = retrieve_relevant_chunks(fq, top_k=5)
                        if batch:
                            all_retrieved_batches.append(batch)
                    except Exception as exc:
                        logger.warning("Follow-up retrieval failed for %r (%s).", fq, exc)

                t_retriever_ms += (time.perf_counter() - t0) * 1000.0
                final_chunks = cls._merge_deduplicate_rerank(all_retrieved_batches, top_k=target_top_k)
            else:
                final_chunks = merged_iter1_chunks

        # Step 5: Check if any chunks cleared similarity threshold
        logger.info("[Step 5] Final Context Selected: %d chunks for LLM prompt.", len(final_chunks))
        if not final_chunks:
            logger.info("No relevant chunks found — returning standard fallback.")
            add_user_message(session_id, question)
            add_assistant_message(session_id, _NO_RELEVANT_CHUNKS_MESSAGE)
            return _NO_RELEVANT_CHUNKS_MESSAGE, []

        # Step 6: Build Grounded Prompt
        logger.info("[Step 6] Building context prompt with %d chunks...", len(final_chunks))
        prompt = build_rag_prompt(question, final_chunks, conversation_history=history)

        # Step 7: Groq LLM Synthesis
        t0 = time.perf_counter()
        logger.info("[Step 7] Invoking Groq LLM for answer synthesis...")
        answer = generate_answer(prompt)
        t_llm_sec = time.perf_counter() - t0

        # Step 8: Update Conversation History & Semantic Cache
        add_user_message(session_id, question)
        add_assistant_message(session_id, answer)

        SemanticCache.set(
            question=retrieval_query,
            answer=answer,
            citations=final_chunks,
            session_id=session_id,
            kb_version=kb_version,
        )

        t_total_sec = time.perf_counter() - start_total

        # Step 9: Emit Structured Performance Telemetry Log
        cls._log_performance_telemetry(
            pipeline_type=intent_result.pipeline,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            cache_status="MISS",
            t_planner_ms=t_planner_ms,
            t_retriever_ms=t_retriever_ms,
            t_reflection_ms=t_reflection_ms,
            second_retrieval=second_retrieval_used,
            chunks_count=len(final_chunks),
            t_llm_sec=t_llm_sec,
            t_total_sec=t_total_sec,
        )

        return answer, final_chunks

    @classmethod
    def _merge_deduplicate_rerank(
        cls, chunk_batches: List[List[Dict[str, Any]]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Merge multiple chunk lists, deduplicate by (document_id, chunk_index), and re-rank.

        Args:
            chunk_batches: List of chunk lists retrieved across queries/turns.
            top_k: Max top candidates to keep (capped at _MAX_CHUNKS_CAP).

        Returns:
            Deduplicated and re-ranked list of top_k chunk dicts.
        """
        top_k = min(top_k, _MAX_CHUNKS_CAP)
        best_chunks: Dict[Tuple[Any, Any], Dict[str, Any]] = {}

        for batch in chunk_batches:
            if not isinstance(batch, list):
                continue
            for chunk in batch:
                if not isinstance(chunk, dict):
                    continue

                doc_id = chunk.get("document_id")
                chunk_idx = chunk.get("chunk_index")

                if doc_id is not None and chunk_idx is not None:
                    key = (doc_id, chunk_idx)
                else:
                    text_snippet = chunk.get("chunk_text", "")
                    key = (doc_id or "unknown", hash(text_snippet))

                existing = best_chunks.get(key)
                score = float(chunk.get("similarity_score", chunk.get("score", 0.0)) or 0.0)

                if existing is None:
                    best_chunks[key] = chunk
                else:
                    existing_score = float(existing.get("similarity_score", existing.get("score", 0.0)) or 0.0)
                    if score > existing_score:
                        best_chunks[key] = chunk

        merged = list(best_chunks.values())
        merged.sort(key=lambda c: float(c.get("similarity_score", c.get("score", 0.0)) or 0.0), reverse=True)
        return merged[:top_k]

    @classmethod
    def _log_intent_result(cls, i: IntentResult, elapsed_ms: float) -> None:
        """Print structured log for Intent Router."""
        logger.info("=== INTENT ROUTER (%.1f ms) ===", elapsed_ms)
        logger.info("Intent Category  : %s", i.intent)
        logger.info("Target Pipeline  : %s", i.pipeline.upper())
        logger.info("Confidence       : %.2f", i.confidence)
        logger.info("Reasoning        : %s", i.reasoning)

    @classmethod
    def _log_planner_result(cls, p: PlannerResult) -> None:
        """Print structured log for Planner Agent results."""
        logger.info("=== PLANNER AGENT ===")
        logger.info("Category         : %s", p.question_category)
        logger.info("Strategy         : %s", p.retrieval_strategy)
        logger.info("Confidence       : %.2f", p.confidence)
        logger.info("Search Queries   : %s", p.search_queries[:_MAX_PLANNER_QUERIES])

    @classmethod
    def _log_reflection_result(cls, r: ReflectionResult, iteration: int, chunk_count: int) -> None:
        """Print structured log for Reflection Agent results."""
        logger.info("=== REFLECTION AGENT (Iteration %d) ===", iteration)
        logger.info("Retrieved Chunks : %d", chunk_count)
        logger.info("Coverage Score   : %.2f", r.coverage_score)
        logger.info("Needs 2nd Round  : %s", r.needs_another_retrieval)

    @classmethod
    def _log_cache_hit(cls, intent_result: IntentResult, total_sec: float) -> None:
        """Log telemetry for Semantic Cache HIT."""
        print("\n========================")
        print("REQUEST (Semantic Cache HIT)")
        print("========================")
        print(f"Intent           : {intent_result.intent} ({intent_result.pipeline.capitalize()})")
        print(f"Confidence       : {intent_result.confidence:.2f}")
        print("Cache            : HIT (>= 0.95 Cosine Similarity)")
        print(f"Total Time       : {total_sec * 1000.0:.1f} ms")
        print("========================\n")

    @classmethod
    def _log_performance_telemetry(
        cls,
        pipeline_type: str,
        intent: str,
        confidence: float,
        cache_status: str,
        t_planner_ms: float,
        t_retriever_ms: float,
        t_reflection_ms: float,
        second_retrieval: str,
        chunks_count: int,
        t_llm_sec: float,
        t_total_sec: float,
    ) -> None:
        """Log structured performance metrics for each completed request."""
        print("\n========================")
        print(f"REQUEST ({pipeline_type.capitalize()} Pipeline)")
        print("========================")
        print(f"Intent           : {intent}")
        print(f"Confidence       : {confidence:.2f}")
        print(f"Cache            : {cache_status}")
        if pipeline_type == "agentic":
            print(f"Planner          : {t_planner_ms:.0f} ms")
        print(f"Retriever        : {t_retriever_ms:.0f} ms")
        if pipeline_type == "agentic":
            print(f"Reflection       : {t_reflection_ms:.0f} ms")
            print(f"Second Retrieval : {second_retrieval}")
        print(f"Chunks           : {chunks_count}")
        print(f"LLM              : {t_llm_sec:.2f} sec")
        print(f"Total            : {t_total_sec:.2f} sec")
        print("========================\n")
