"""HTTP endpoint coordinating the Agentic RAG pipeline, citations, and HTTP responses."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.retrieval_controller import RetrievalController
from app.services.llm_service import LLMConfigurationError, LLMServiceError, LLMTimeoutError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    query: str


class SourceCitation(BaseModel):
    """Public metadata for one chunk used to ground an answer."""

    document_id: int | None
    filename: str | None = None
    page_number: int | None = 1
    chunk_index: int | None
    score: float
    snippet: str | None = None
    character_start: int | None = 0
    character_end: int | None = 0


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceCitation] = Field(default_factory=list)


def _build_sources(retrieved_chunks: list[dict]) -> list[SourceCitation]:
    """Convert internal retrieval records to public citation metadata only."""
    return [
        SourceCitation(
            document_id=chunk.get("document_id"),
            filename=chunk.get("filename") or chunk.get("original_filename"),
            page_number=chunk.get("page_number", 1),
            chunk_index=chunk.get("chunk_index"),
            score=float(chunk.get("similarity_score", chunk.get("score", 0.0)) or 0.0),
            snippet=chunk.get("chunk_text"),
            character_start=chunk.get("character_start", 0),
            character_end=chunk.get("character_end", 0),
        )
        for chunk in retrieved_chunks
        if isinstance(chunk, dict)
    ]


@router.post("/chat")
def chat(payload: ChatRequest) -> ChatResponse:
    """Answer a question using the Agentic Retrieval Pipeline (Planner -> Controller -> Hybrid -> Reflection)."""
    session_id = payload.session_id.strip() if isinstance(payload.session_id, str) else ""
    question = payload.query.strip() if isinstance(payload.query, str) else ""
    if not session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session ID cannot be empty")
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

    logger.info("Chat endpoint received request for session %s...", session_id)

    try:
        answer, retrieved_chunks = RetrievalController.process_chat_request(session_id, question)
    except LLMTimeoutError as exc:
        logger.error("Groq request timed out during Agentic RAG execution")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Answer generation timed out",
        ) from exc
    except LLMConfigurationError as exc:
        logger.error("Groq is not configured: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation is not configured",
        ) from exc
    except LLMServiceError as exc:
        logger.error("LLM service error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Answer generation is currently unavailable",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in Agentic RAG execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request",
        ) from exc

    return ChatResponse(
        question=question,
        answer=answer,
        sources=_build_sources(retrieved_chunks),
    )
