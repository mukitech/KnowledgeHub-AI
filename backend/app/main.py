from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat_routes import router as chat_router
from app.api.document_routes import router as document_router
from app.api.routes import router
from app.core.qdrant import initialize_qdrant
from app.database.database import Base, engine
from app.models.document import Document  # noqa: F401
from app.services.embedding_service import initialize_embedding_model

app = FastAPI(
    title="KnowledgeHub AI",
    description="Enterprise AI Knowledge Assistant using RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://knowledge-hub-ai-orcin.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _migrate_documents_table() -> None:
    """Add new metadata columns to the existing *documents* table if absent.

    ``Base.metadata.create_all`` only creates missing *tables*, not missing
    *columns*.  This lightweight migration fills that gap without requiring
    Alembic.  Each statement is idempotent (``IF NOT EXISTS``).
    """
    new_columns = [
        ("title",        "VARCHAR(500)"),
        ("author",       "VARCHAR(255)"),
        ("summary",      "TEXT"),
        ("keywords",     "TEXT"),
        ("topics",       "TEXT"),
        ("language",     "VARCHAR(50)"),
        ("total_pages",  "INTEGER"),
        ("total_chunks", "INTEGER"),
    ]
    with engine.begin() as conn:
        for col_name, col_type in new_columns:
            conn.execute(
                text(
                    f"ALTER TABLE documents "
                    f"ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                )
            )


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_documents_table()
    initialize_embedding_model()
    initialize_qdrant()


app.include_router(router)
app.include_router(document_router)
app.include_router(chat_router)

