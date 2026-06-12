"""
Cross-encoder reranker using cross-encoder/ms-marco-MiniLM-L-6-v2.

Takes (query, [candidate chunks]) and returns re-scored candidates
sorted by relevance descending.
"""

from __future__ import annotations

from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    _instance: "CrossEncoderReranker | None" = None

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        print(f"[Reranker] Loading model: {model_name}")
        self.model = CrossEncoder(model_name, max_length=512)
        self.model_name = model_name
        print("[Reranker] Model loaded")

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Re-rank candidate chunks by relevance to query.

        candidates: list of dicts, each must have 'content' key.
        Returns top_k dicts with added 'rerank_score' field, sorted desc.
        """
        if not candidates:
            return []

        pairs = [(query, c["content"]) for c in candidates]
        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


# Module-level lazy singleton
_reranker: CrossEncoderReranker | None = None


def get_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> CrossEncoderReranker:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker(model_name)
    return _reranker