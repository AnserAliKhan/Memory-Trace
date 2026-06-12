"""
Application configuration loaded from environment / .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Database
    database_url: str = "sqlite:///./refound.db"

    # FAISS
    faiss_index_path: str = "./faiss_index"
    embedding_dim: int = 384  # bge-small-en-v1.5 output dim

    # Models
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Retrieval
    top_k_retrieval: int = 20
    top_k_rerank: int = 5

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64

    # CORS
    frontend_origin: str = "http://localhost:5173"


@lru_cache()
def get_settings() -> Settings:
    return Settings()