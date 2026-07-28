from typing import List, Optional

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_embedding_model: Optional[SentenceTransformer] = None


def initialize_embedding_model() -> SentenceTransformer:
    """Load the sentence-transformer model once at startup and cache it for reuse."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(MODEL_NAME)
    return _embedding_model


def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """Convert a list of text chunks into one embedding vector per chunk."""
    if not chunks:
        return []

    model = initialize_embedding_model()
    embeddings = model.encode(chunks, convert_to_tensor=False, normalize_embeddings=False)

    return [embedding.tolist() if hasattr(embedding, "tolist") else list(embedding) for embedding in embeddings]
