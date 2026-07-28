from pathlib import Path
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

COLLECTION_NAME = "knowledgehub_documents"
VECTOR_SIZE = 384
DISTANCE_METRIC = Distance.COSINE
# Minimum cosine-similarity score a retrieved chunk must reach to be used as context.
# Raise this to demand tighter matches; lower it to allow more lenient recall.
SIMILARITY_THRESHOLD = 0.45
QDRANT_STORAGE_DIR = (Path(__file__).resolve().parent.parent.parent / "qdrant_storage").resolve()
QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
QDRANT_PATH = str(QDRANT_STORAGE_DIR)

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """Return a shared Qdrant client instance, creating it once per process."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=QDRANT_PATH)
    return _qdrant_client


def ensure_collection_exists() -> None:
    """Create the collection if it does not already exist."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    if any(collection.name == COLLECTION_NAME for collection in collections):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=DISTANCE_METRIC),
    )


def initialize_qdrant() -> None:
    """Ensure the shared client and collection are ready for use."""
    ensure_collection_exists()
