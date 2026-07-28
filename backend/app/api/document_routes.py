import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Path as FastAPIPath, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentDeletionResponse, DocumentStats, DocumentSummary
from app.services.chunking_service import chunk_pages, chunk_text
from app.services.document_service import delete_document, list_documents, save_upload_document, update_document_metadata
from app.services.embedding_service import generate_embeddings
from app.services.metadata_service import generate_document_metadata
from app.services.pdf_service import extract_pages, extract_text
from app.services.retriever import retrieve_relevant_chunks
from app.services.vector_store import get_vector_count, store_embeddings

router = APIRouter(prefix="/documents", tags=["documents"])


class SearchRequest(BaseModel):
    query: str


@router.get("", response_model=list[DocumentSummary])
def get_documents(db: Session = Depends(get_db)) -> list[DocumentSummary]:
    """List all uploaded documents, newest first, including AI metadata and stats."""
    return [
        DocumentSummary(
            id=document.id,
            filename=document.original_filename,
            uploaded_at=document.uploaded_at,
            title=document.title,
            author=document.author,
            summary=document.summary,
            keywords=document.keywords,
            topics=document.topics,
            language=document.language,
            processing_status=document.processing_status,
            total_pages=document.total_pages,
            total_chunks=document.total_chunks,
        )
        for document in list_documents(db)
    ]


@router.get("/stats", response_model=DocumentStats)
def get_document_stats(db: Session = Depends(get_db)) -> DocumentStats:
    """Return aggregate statistics across all uploaded documents."""
    docs = list_documents(db)
    total_documents = len(docs)
    total_vectors = get_vector_count()

    # Backfill legacy document rows missing page counts from stored PDF files
    needs_commit = False
    for doc in docs:
        if doc.total_pages is None and doc.file_path and os.path.exists(doc.file_path):
            try:
                import fitz
                pdf = fitz.open(doc.file_path)
                doc.total_pages = pdf.page_count
                pdf.close()
                needs_commit = True
            except Exception:
                pass

    if needs_commit:
        try:
            db.commit()
        except Exception:
            db.rollback()

    total_pages = sum(d.total_pages or 0 for d in docs)
    sum_chunks = sum(d.total_chunks or 0 for d in docs)
    # If legacy documents lack stored chunk counts, fallback to total vector count
    total_chunks = sum_chunks if sum_chunks > 0 else total_vectors

    avg_chunks = round(total_chunks / total_documents, 2) if total_documents else 0.0
    last_upload = max((d.uploaded_at for d in docs), default=None)

    return DocumentStats(
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_pages=total_pages,
        total_vectors=total_vectors,
        avg_chunks_per_document=avg_chunks,
        last_upload_at=last_upload,
    )


@router.delete("/{document_id}", response_model=DocumentDeletionResponse)
def delete_uploaded_document(
    document_id: int = FastAPIPath(ge=1),
    db: Session = Depends(get_db),
) -> DocumentDeletionResponse:
    """Remove a document's vectors first, then its database record."""
    try:
        deleted = delete_document(document_id, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete document",
        ) from exc

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    from app.services.semantic_cache import SemanticCache
    SemanticCache.invalidate_cache()

    return DocumentDeletionResponse(
        message="Document deleted successfully",
        document_id=document_id,
    )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return await save_upload_document(file, db)


@router.post("/test-extract")
async def test_extract_document(file: UploadFile = File(...)):
    temp_file_path = None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        temp_file.write(content)
        temp_file.flush()
        temp_file_path = Path(temp_file.name)

    try:
        extracted_text = extract_text(str(temp_file_path))
        page_count = extracted_text.count("\n\n") + 1
        character_count = len(extracted_text)
        text_preview = extracted_text[:1000]

        return {
            "page_count": page_count,
            "character_count": character_count,
            "text_preview": text_preview,
        }
    finally:
        if temp_file_path is not None and temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@router.post("/test-chunk")
async def test_chunk_document(file: UploadFile = File(...)):
    temp_file_path = None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        temp_file.write(content)
        temp_file.flush()
        temp_file_path = Path(temp_file.name)

    try:
        extracted_text = extract_text(str(temp_file_path))
        chunks = chunk_text(extracted_text)

        return {
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "chunk_index": item["chunk_index"],
                    "character_start": item["character_start"],
                    "character_end": item["character_end"],
                    "preview": item["chunk_text"][:300],
                }
                for item in chunks
            ],
        }
    finally:
        if temp_file_path is not None and temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@router.post("/test-embedding")
async def test_embedding_document(file: UploadFile = File(...)):
    temp_file_path = None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        temp_file.write(content)
        temp_file.flush()
        temp_file_path = Path(temp_file.name)

    try:
        extracted_text = extract_text(str(temp_file_path))
        chunks = [item["chunk_text"] for item in chunk_text(extracted_text)]
        embeddings = generate_embeddings(chunks)

        return {
            "total_chunks": len(chunks),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "sample_embedding": embeddings[0][:10] if embeddings else [],
        }
    finally:
        if temp_file_path is not None and temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@router.post("/test-store")
async def test_store_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print("Step 1: upload received")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    temp_file_path = None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file.write(content)
        temp_file.flush()
        temp_file_path = Path(temp_file.name)

    try:
        print("Step 2: extracting text")
        extracted_pages = extract_pages(str(temp_file_path))
        full_text = "\n\n".join(p["text"] for p in extracted_pages)

        print("Step 3: generating AI metadata via Groq")
        metadata = generate_document_metadata(full_text)
        print(f"  title={metadata.get('title')!r}  author={metadata.get('author')!r}  language={metadata.get('language')!r}")

        print("Step 4: chunking pages")
        chunk_items = chunk_pages(extracted_pages)
        if not chunk_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No text could be chunked")

        chunks = [item["chunk_text"] for item in chunk_items]
        print("Step 5: generating embeddings")
        embeddings = generate_embeddings(chunks)

        if len(chunks) != len(embeddings):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Embedding count mismatch")

        print("Step 6: saving upload to database")
        await file.seek(0)
        document_result = await save_upload_document(file, db)

        print("Step 7: saving AI metadata and structure stats to database")
        metadata["total_pages"]  = len(extracted_pages)
        metadata["total_chunks"] = len(chunk_items)
        update_document_metadata(document_result["id"], metadata, db)

        print("Step 8: storing embeddings in Qdrant")
        stored_count = store_embeddings(
            document_result["id"],
            chunk_items,
            embeddings,
            filename=file.filename,
        )

        from app.services.semantic_cache import SemanticCache
        SemanticCache.invalidate_cache()

        print("Step 9: returning response")
        return {
            "document_id": document_result["id"],
            "chunks_stored": stored_count,
            "collection": "knowledgehub_documents",
            "status": "success",
            "metadata": metadata,
        }
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        if temp_file_path is not None and temp_file_path.exists():
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


@router.get("/vector-count")
async def get_vector_count_endpoint():
    return {
        "collection": "knowledgehub_documents",
        "total_vectors": get_vector_count(),
    }


@router.get("/{document_id}/file")
def get_document_file(
    document_id: int = FastAPIPath(ge=1),
    db: Session = Depends(get_db),
):
    """Serve the stored PDF binary file stream for PDF viewing."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file missing on server")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=document.original_filename,
    )


@router.post("/test-search")
async def test_search_document(payload: SearchRequest):
    query = payload.query
    if not query or not str(query).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")

    try:
        results = retrieve_relevant_chunks(query, top_k=5)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if not results:
        return {"message": "No indexed documents found."}

    return {
        "query": query,
        "top_k": 5,
        "results": results,
    }
