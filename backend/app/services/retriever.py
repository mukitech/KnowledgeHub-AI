"""Hybrid Search Retriever service combining Qdrant Vector Search & BM25 Keyword Search.

Hybrid Retrieval Pipeline:
1. Dense Vector Search via Qdrant (cosine similarity)
2. Sparse Keyword Search via rank-bm25 over all indexed chunks
3. Reciprocal Rank & Normalized Score Fusion with duplicate boosting
4. Filtering against configurable similarity threshold
"""

import logging
import re
from typing import Any, Dict, List, Set

from rank_bm25 import BM25Okapi

from app.core.qdrant import COLLECTION_NAME, SIMILARITY_THRESHOLD, ensure_collection_exists, get_qdrant_client
from app.database.database import SessionLocal
from app.models.document import Document
from app.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Retrieve the most relevant indexed chunks using Hybrid Search (Vector + BM25).

    Args:
        query: User search query string.
        top_k: Number of top relevant chunks to return (default 5).

    Returns:
        List of dicts containing document_id, filename, page_number, chunk_index,
        chunk_text, character_start, character_end, similarity_score, and score.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    clean_query = query.strip()
    logger.info("Hybrid Retriever: receiving query %r", clean_query)

    ensure_collection_exists()
    client = get_qdrant_client()

    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    total_points = getattr(collection_info, "points_count", 0) or 0
    if total_points == 0:
        logger.info("Hybrid Retriever: collection is empty (0 points).")
        return []

    # ---------------------------------------------------------------------------
    # Step 1: Dense Vector Search (Qdrant)
    # ---------------------------------------------------------------------------
    logger.info("Generating query embedding for vector search...")
    query_embedding = generate_embeddings([clean_query])[0]

    vector_candidate_limit = max(top_k * 3, 15)
    logger.info("Searching Qdrant vector index (limit=%d)...", vector_candidate_limit)
    qdrant_points = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=vector_candidate_limit,
        with_payload=True,
    ).points

    # ---------------------------------------------------------------------------
    # Step 2: Fetch all indexed chunks for BM25 Keyword Search
    # ---------------------------------------------------------------------------
    logger.info("Fetching all %d indexed chunks for BM25 keyword search...", total_points)
    scroll_records, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=min(total_points, 10000),
        with_payload=True,
        with_vectors=False,
    )

    all_chunks_map: Dict[str, Dict[str, Any]] = {}
    corpus_tokens: List[List[str]] = []
    chunk_point_ids: List[str] = []

    for point in scroll_records:
        pid = str(point.id)
        payload = point.payload or {}
        chunk_text = payload.get("chunk_text", "")
        
        all_chunks_map[pid] = {
            "id": pid,
            "payload": payload,
            "text": chunk_text,
        }
        corpus_tokens.append(_tokenize(chunk_text))
        chunk_point_ids.append(pid)

    # ---------------------------------------------------------------------------
    # Step 3: Sparse Keyword Search (BM25)
    # ---------------------------------------------------------------------------
    query_tokens = _tokenize(clean_query)
    bm25_scores: Dict[str, float] = {}

    if corpus_tokens and query_tokens:
        logger.info("Running BM25 keyword search over %d chunks...", len(corpus_tokens))
        bm25 = BM25Okapi(corpus_tokens)
        doc_scores = bm25.get_scores(query_tokens)
        for pid, score in zip(chunk_point_ids, doc_scores):
            bm25_scores[pid] = float(score)

    # ---------------------------------------------------------------------------
    # Step 4: Hybrid Merging, Normalization & Duplicate Boosting
    # ---------------------------------------------------------------------------
    vector_scores: Dict[str, float] = {}
    for p in qdrant_points:
        pid = str(p.id)
        vector_scores[pid] = float(getattr(p, "score", 0.0) or 0.0)
        # Ensure payload is saved if scroll missed it
        if pid not in all_chunks_map:
            all_chunks_map[pid] = {
                "id": pid,
                "payload": p.payload or {},
                "text": (p.payload or {}).get("chunk_text", ""),
            }

    # Top sets for dual-hit detection
    top_vector_pids: Set[str] = set(
        sorted(vector_scores.keys(), key=lambda k: vector_scores[k], reverse=True)[:top_k]
    )
    top_bm25_pids: Set[str] = set(
        sorted(bm25_scores.keys(), key=lambda k: bm25_scores[k], reverse=True)[:top_k]
    )

    max_vector_score = max(vector_scores.values(), default=1.0) or 1.0
    max_bm25_score = max(bm25_scores.values(), default=1.0) or 1.0

    # Combine candidates from both searches
    all_candidate_pids = set(vector_scores.keys()).union(
        sorted(bm25_scores.keys(), key=lambda k: bm25_scores[k], reverse=True)[:top_k * 2]
    )

    # Filename DB lookup cache for legacy payloads
    doc_filenames: Dict[int, str] = {}

    merged_results: List[Dict[str, Any]] = []
    for pid in all_candidate_pids:
        chunk_data = all_chunks_map.get(pid)
        if not chunk_data:
            continue

        payload = chunk_data["payload"]
        v_score = vector_scores.get(pid, 0.0)
        b_score = bm25_scores.get(pid, 0.0)

        # Normalize vector and BM25 scores to [0, 1] range
        v_norm = max(0.0, v_score / max_vector_score) if max_vector_score > 0 else 0.0
        b_norm = max(0.0, b_score / max_bm25_score) if max_bm25_score > 0 else 0.0

        # Weighted hybrid score (60% vector + 40% BM25)
        hybrid_score = (0.6 * v_norm) + (0.4 * b_norm)

        # Requirement 5: If chunk appears in top results of BOTH searches, boost score by 15%
        in_both = (pid in top_vector_pids) and (pid in top_bm25_pids)
        if in_both:
            hybrid_score *= 1.15
            logger.info("Hybrid Retriever: chunk %s present in both searches — boosted score to %.3f", pid, hybrid_score)

        # Use vector score if available for baseline similarity score, else hybrid score
        final_similarity_score = round(float(v_score if v_score > 0 else hybrid_score), 4)

        doc_id = payload.get("document_id")
        filename = payload.get("filename") or payload.get("original_filename")

        if not filename and doc_id:
            if doc_id not in doc_filenames:
                try:
                    with SessionLocal() as db:
                        doc = db.get(Document, int(doc_id))
                        if doc and doc.original_filename:
                            doc_filenames[doc_id] = doc.original_filename
                except Exception:
                    pass
            filename = doc_filenames.get(doc_id, f"Document #{doc_id}")

        merged_results.append(
            {
                "document_id": doc_id,
                "filename": filename or (f"Document #{doc_id}" if doc_id else "Document"),
                "chunk_index": payload.get("chunk_index"),
                "chunk_text": payload.get("chunk_text", ""),
                "page_number": int(payload.get("page_number", 1) or 1),
                "character_start": int(payload.get("character_start", 0) or 0),
                "character_end": int(payload.get("character_end", 0) or 0),
                "similarity_score": final_similarity_score,
                "score": final_similarity_score,
                "hybrid_score": round(hybrid_score, 4),
            }
        )

    # Sort merged results by hybrid_score descending
    merged_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

    # ---------------------------------------------------------------------------
    # Step 5: Filter by similarity threshold & return Top K
    # ---------------------------------------------------------------------------
    filtered = [r for r in merged_results if r["similarity_score"] >= SIMILARITY_THRESHOLD]
    top_results = filtered[:top_k]

    logger.info(
        "Hybrid Retriever: retrieved %d merged candidates → %d above threshold %.2f → top %d returned.",
        len(merged_results),
        len(filtered),
        SIMILARITY_THRESHOLD,
        len(top_results),
    )

    return top_results


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words for BM25 keyword matching."""
    if not text or not isinstance(text, str):
        return []
    return re.findall(r"\w+", text.lower())
