from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.vector_store import delete_document_vectors

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_document(file: UploadFile, db: Session) -> dict:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected",
        )

    filename = file.filename.lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    extension = Path(file.filename).suffix.lower()
    saved_filename = f"{uuid4().hex}{extension}"
    save_path = UPLOAD_DIR / saved_filename

    with save_path.open("wb") as destination:
        destination.write(content)

    document = Document(
        original_filename=file.filename,
        stored_filename=saved_filename,
        file_path=str(save_path),
        file_size=len(content),
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "stored_filename": document.stored_filename,
        "processing_status": document.processing_status,
    }


def list_documents(db: Session) -> list[Document]:
    """Return uploaded documents ordered from newest to oldest."""
    statement = select(Document).order_by(Document.uploaded_at.desc(), Document.id.desc())
    return list(db.scalars(statement))


def delete_document(document_id: int, db: Session) -> bool:
    """Delete a document's Qdrant vectors, then its PostgreSQL record."""
    document = db.get(Document, document_id)
    if document is None:
        return False

    try:
        # Do not remove the relational record until Qdrant confirms deletion.
        delete_document_vectors(document_id)
        db.delete(document)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True


def update_document_metadata(document_id: int, metadata: dict, db: Session) -> None:
    """Write AI-generated metadata fields onto an existing document row.

    Only fields present (and non-None) in *metadata* are written, so partial
    updates are safe.  The function is a no-op if the document is not found.
    """
    document = db.get(Document, document_id)
    if document is None:
        return

    updatable = ("title", "author", "summary", "keywords", "topics", "language", "total_pages", "total_chunks")
    for field in updatable:
        value = metadata.get(field)
        if value is not None:
            setattr(document, field, value)

    document.processing_status = "PROCESSED"
    db.commit()
    db.refresh(document)
