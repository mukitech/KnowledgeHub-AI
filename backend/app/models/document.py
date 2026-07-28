from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    processing_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UPLOADED",
    )

    # --- AI-generated metadata (populated after upload) ---
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Stored as comma-separated values for simplicity (no extra JSON dependency)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- Document structure stats (populated after ingestion) ---
    total_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_chunks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
