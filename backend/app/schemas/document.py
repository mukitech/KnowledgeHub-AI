"""Response schemas for document-management endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    processing_status: Optional[str] = None
    # AI-generated metadata (None until processing completes)
    title: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[str] = None   # comma-separated
    topics: Optional[str] = None     # comma-separated
    language: Optional[str] = None
    # Document structure stats
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None


class DocumentStats(BaseModel):
    """Aggregate statistics across all uploaded documents."""
    total_documents: int
    total_chunks: int
    total_pages: int
    total_vectors: int
    avg_chunks_per_document: float
    last_upload_at: Optional[datetime] = None


class DocumentDeletionResponse(BaseModel):
    message: str
    document_id: int

