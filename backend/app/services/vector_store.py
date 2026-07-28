from typing import Dict, List
from uuid import NAMESPACE_URL, uuid5

from qdrant_client.http import models

from app.core.qdrant import COLLECTION_NAME, ensure_collection_exists, get_qdrant_client


def _build_point_id(document_id: int, chunk_index: int) -> str:
    """Create a deterministic UUID string so repeated uploads overwrite the same chunk entries."""
    return str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk_index}"))


def store_embeddings(
    document_id: int,
    chunks: List[Dict[str, object]],
    embeddings: List[List[float]],
    filename: str | None = None,
) -> int:
    """Store chunk embeddings in Qdrant with document and chunk metadata in the payload."""
    ensure_collection_exists()
    client = get_qdrant_client()

    if len(chunks) != len(embeddings):
        raise ValueError("Chunk count and embedding count must match")

    points = []
    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_text = chunk.get("chunk_text")
        if not isinstance(chunk_text, str):
            raise ValueError(f"Chunk at index {index} is missing valid text")

        points.append(
            models.PointStruct(
                id=_build_point_id(document_id, index),
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "filename": filename or "",
                    "chunk_index": index,
                    "chunk_text": chunk_text,
                    "page_number": int(chunk.get("page_number", 1) or 1),
                    "character_start": int(chunk.get("character_start", 0) or 0),
                    "character_end": int(chunk.get("character_end", 0) or 0),
                },
            )
        )

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    return len(points)


def get_vector_count() -> int:
    """Return the number of stored vectors in the collection."""
    ensure_collection_exists()
    client = get_qdrant_client()
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)
    return int(getattr(collection_info, "points_count", 0) or 0)


def delete_document_vectors(document_id: int) -> None:
    """Delete all vectors whose payload belongs to one document."""
    ensure_collection_exists()
    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document_id),
                )
            ]
        ),
    )
