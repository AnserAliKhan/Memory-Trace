"""
Local embedding encoder using BAAI/bge-small-en-v1.5.

BGE models expect a query prefix for asymmetric search:
  - Queries:   "Represent this sentence for searching relevant passages: {query}"
  - Documents: raw text (no prefix)
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class EmbeddingEncoder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        print(f"[Embeddings] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dim = self.model.get_sentence_embedding_dimension()
        print(f"[Embeddings] Model loaded. Dimension: {self.dim}")

    def encode_documents(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode a list of document texts. Returns (N, dim) float32 array."""
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single search query with BGE prefix. Returns (1, dim) float32."""
        prefixed = QUERY_PREFIX + query
        embedding = self.model.encode(
            [prefixed],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding.astype(np.float32)