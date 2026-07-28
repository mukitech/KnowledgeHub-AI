"""Semantic Cache service for KnowledgeHub AI.

Provides fast vector-similarity caching for user questions using 384-D sentence embeddings.
Bypasses retrieval and LLM generation when an incoming question has >= 0.95 cosine similarity
with a previously answered query in the same Knowledge Base version.

Supports automatic cache invalidation on document uploads, deletions, or vector rebuilds.
"""

from datetime import datetime, timezone
import logging
import math
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)

# Global cache invalidation version counter
_kb_version_counter: int = 1
_cached_entries: List["CachedResponse"] = []


class CachedResponse(BaseModel):
    """Data model representing a stored semantic cache entry."""

    question: str = Field(description="Raw user question string")
    answer: str = Field(description="Synthesized grounded answer")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved source citations")
    embedding: List[float] = Field(description="384-D sentence embedding vector")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str = Field(description="Session ID where response was generated")
    kb_version: str = Field(description="Knowledge base version string during caching")


class SemanticCache:
    """Enterprise in-memory Semantic Cache service."""

    @classmethod
    def get_kb_version(cls) -> str:
        """Return current global Knowledge Base version string."""
        global _kb_version_counter
        return f"v{_kb_version_counter}"

    @classmethod
    def invalidate_cache(cls) -> None:
        """Invalidate all cached responses by clearing cache and bumping KB version counter."""
        global _kb_version_counter, _cached_entries
        _kb_version_counter += 1
        cleared_count = len(_cached_entries)
        _cached_entries.clear()
        logger.info("[SemanticCache] Cache invalidated! Cleared %d entries. New KB Version: v%d", cleared_count, _kb_version_counter)

    @classmethod
    def get(
        cls,
        question: str,
        session_id: str,
        kb_version: str,
        threshold: float = 0.95,
    ) -> Optional[CachedResponse]:
        """Search cache for a semantically matching question with cosine similarity >= threshold.

        Args:
            question: Clean input user query.
            session_id: Current session identifier.
            kb_version: Current Knowledge Base version string.
            threshold: Minimum cosine similarity threshold (default 0.95).

        Returns:
            CachedResponse if a match is found, else None.
        """
        global _cached_entries
        if not _cached_entries:
            return None

        # Generate 384-D vector embedding for input question
        try:
            embeddings = generate_embeddings([question])
            if not embeddings or not embeddings[0]:
                return None
            q_vec = embeddings[0]
        except Exception as exc:
            logger.warning("[SemanticCache] Failed to generate query embedding for cache lookup: %s", exc)
            return None

        best_match: Optional[CachedResponse] = None
        best_sim: float = -1.0

        for entry in _cached_entries:
            # Skip invalid KB versions
            if entry.kb_version != kb_version:
                continue

            sim = cls._cosine_similarity(q_vec, entry.embedding)
            if sim > best_sim:
                best_sim = sim
                best_match = entry

        if best_match and best_sim >= threshold:
            logger.info(
                "[SemanticCache] HIT! Similarity: %.4f >= %.2f | Matched question: %r",
                best_sim,
                threshold,
                best_match.question,
            )
            return best_match

        logger.info("[SemanticCache] MISS (Best similarity: %.4f < %.2f)", best_sim if best_sim > 0 else 0.0, threshold)
        return None

    @classmethod
    def set(
        cls,
        question: str,
        answer: str,
        citations: List[Dict[str, Any]],
        session_id: str,
        kb_version: str,
    ) -> None:
        """Store a new Q&A pair in the semantic cache.

        Args:
            question: User question string.
            answer: Synthesized answer string.
            citations: Grounded citation list.
            session_id: Active session identifier.
            kb_version: Current Knowledge Base version string.
        """
        global _cached_entries
        try:
            embeddings = generate_embeddings([question])
            if not embeddings or not embeddings[0]:
                return
            q_vec = embeddings[0]
        except Exception as exc:
            logger.warning("[SemanticCache] Failed to generate query embedding for caching: %s", exc)
            return

        entry = CachedResponse(
            question=question,
            answer=answer,
            citations=citations,
            embedding=q_vec,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            kb_version=kb_version,
        )

        _cached_entries.append(entry)
        logger.info("[SemanticCache] STORED entry for question: %r (Total cached: %d)", question, len(_cached_entries))

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vector floats."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_prod = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot_prod / (norm1 * norm2)
