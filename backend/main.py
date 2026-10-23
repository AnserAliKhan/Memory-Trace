"""
ReFound — FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, query, settings, health
from app.database.session import init_db
from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    cfg = get_settings()
    init_db()

    # Pre-load embedding model and FAISS index into app state
    from app.embeddings.encoder import EmbeddingEncoder
    from app.retrieval.index import FAISSIndex

    app.state.encoder = EmbeddingEncoder(cfg.embedding_model)
    app.state.faiss_index = FAISSIndex(cfg.faiss_index_path, cfg.embedding_dim)
    app.state.faiss_index.load_if_exists()

    yield

    # Shutdown: persist FAISS index
    app.state.faiss_index.save()


def create_app() -> FastAPI:
    cfg = get_settings()

    app = FastAPI(
        title="ReFound API",
        description="Local-first memory retrieval system",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[cfg.frontend_origin, "http://localhost:5173"],
        allow_origin_regex=cfg.cors_origin_regex or None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(query.router, prefix="/api/query", tags=["query"])
    app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

    return app


app = create_app()