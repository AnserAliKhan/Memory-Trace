"""
Query pipeline route: embed → FAISS → rerank → Gemini.
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import Chunk, Document, QueryHistory
from app.reranker.reranker import get_reranker
from app.llm.gemini import GeminiClient
from config import get_settings

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/")
async def run_query(req: QueryRequest, request: Request, db: Session = Depends(get_db)):
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    cfg = get_settings()
    start = time.time()

    # Encode
    encoder = request.app.state.encoder
    query_embedding = encoder.encode_query(req.query)

    # FAISS search
    faiss_index = request.app.state.faiss_index
    results = faiss_index.search(query_embedding, top_k=cfg.top_k_retrieval)

    if not results:
        return {
            "answer": "No relevant memories found. Import some documents first.",
            "sources": [],
            "similar_problems": [],
            "duration_ms": (time.time() - start) * 1000,
        }

    # Fetch chunks + docs from DB
    chunk_ids = [r["chunk_id"] for r in results]
    score_map = {r["chunk_id"]: r["score"] for r in results}

    chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
    chunk_map = {c.id: c for c in chunks}

    doc_ids = {c.document_id for c in chunks}
    docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    doc_map = {d.id: d for d in docs}

    candidates = []
    for chunk_id in chunk_ids:
        chunk = chunk_map.get(chunk_id)
        if not chunk:
            continue
        doc = doc_map.get(chunk.document_id)
        candidates.append({
            "content": chunk.content,
            "source": doc.title if doc else "Unknown",
            "filename": doc.filename if doc else "",
            "score": score_map.get(chunk_id, 0.0),
            "chunk_id": chunk_id,
            "document_id": chunk.document_id,
        })

    # Rerank
    top_k = min(req.top_k, len(candidates))
    reranker = get_reranker(cfg.reranker_model)
    reranked = reranker.rerank(req.query, candidates, top_k=top_k)

    # Gemini synthesis
    if not cfg.gemini_api_key:
        answer = "[GEMINI_API_KEY not set] Top result: " + (reranked[0]["content"] if reranked else "")
    else:
        try:
            gemini = GeminiClient(cfg.gemini_api_key, cfg.gemini_model)
            answer = gemini.synthesize_answer(req.query, reranked)
        except Exception as e:
            answer = f"LLM error: {e}"

    sources = [
        {
            "source": c["source"],
            "filename": c.get("filename", ""),
            "score": round(c.get("rerank_score", c["score"]), 4),
            "excerpt": c["content"][:300],
        }
        for c in reranked
    ]

    duration_ms = round((time.time() - start) * 1000, 2)

    # Persist history
    try:
        history = QueryHistory(
            query_text=req.query,
            answer=answer,
            sources=sources,
            duration_ms=duration_ms,
        )
        db.add(history)
        db.commit()
    except Exception:
        pass  # history failure shouldn't break response

    return {
        "answer": answer,
        "sources": sources,
        "similar_problems": [],
        "duration_ms": duration_ms,
    }


@router.get("/history")
async def get_history(db: Session = Depends(get_db), limit: int = 20):
    rows = db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return [r.to_dict() for r in rows]