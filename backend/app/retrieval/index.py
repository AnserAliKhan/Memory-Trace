"""
FAISS flat inner-product index.

Embeddings are L2-normalized before insertion so inner product == cosine similarity.

Index file layout:
  {path}.index   — FAISS binary index
  {path}.ids     — numpy int64 array mapping FAISS row → chunk DB id
"""

from __future__ import annotations

import os
import numpy as np

import faiss


class FAISSIndex:
    def __init__(self, index_path: str, dim: int = 384):
        self.index_path = index_path
        self.ids_path = index_path + ".ids.npy"
        self.faiss_path = index_path + ".index"
        self.dim = dim

        # Inner-product index (cosine when vectors are normalized)
        self._index = faiss.IndexFlatIP(dim)
        self._ids: list[int] = []  # parallel array: FAISS row → chunk DB id

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_if_exists(self):
        if os.path.exists(self.faiss_path) and os.path.exists(self.ids_path):
            print(f"[FAISS] Loading index from {self.faiss_path}")
            self._index = faiss.read_index(self.faiss_path)
            self._ids = np.load(self.ids_path, allow_pickle=False).tolist()
            print(f"[FAISS] Loaded {self._index.ntotal} vectors")
        else:
            print("[FAISS] No existing index found, starting fresh")

    def save(self):
        os.makedirs(os.path.dirname(self.faiss_path) or ".", exist_ok=True)
        faiss.write_index(self._index, self.faiss_path)
        np.save(self.ids_path, np.array(self._ids, dtype=np.int64))
        print(f"[FAISS] Saved {self._index.ntotal} vectors to {self.faiss_path}")

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, embeddings: np.ndarray, chunk_ids: list[int]):
        """
        Add embeddings to the index.
        embeddings: (N, dim) float32, already L2-normalized
        chunk_ids:  list of DB chunk ids, length N
        """
        if embeddings.shape[0] == 0:
            return
        self._index.add(embeddings)
        self._ids.extend(chunk_ids)

    def remove_by_chunk_ids(self, chunk_ids: set[int]):
        """
        FAISS flat indices don't support in-place removal.
        We rebuild the index excluding the given chunk ids.
        """
        if not chunk_ids:
            return
        all_vectors = self._index.reconstruct_n(0, self._index.ntotal)
        keep_mask = [cid not in chunk_ids for cid in self._ids]

        kept_vecs = all_vectors[keep_mask]
        kept_ids = [cid for cid, keep in zip(self._ids, keep_mask) if keep]

        self._index = faiss.IndexFlatIP(self.dim)
        self._ids = []
        if len(kept_vecs) > 0:
            self.add(kept_vecs.astype(np.float32), kept_ids)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query_embedding: np.ndarray, top_k: int) -> list[dict]:
        """
        Search for top_k nearest chunks.

        Returns list of {"chunk_id": int, "score": float} dicts,
        sorted by descending score.
        """
        if self._index.ntotal == 0:
            return []

        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk_id = self._ids[idx]
            results.append({"chunk_id": chunk_id, "score": float(score)})

        return results

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal