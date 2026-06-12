"""
SQLAlchemy ORM models for ReFound.

Tables:
  - documents     : imported source files
  - chunks        : text chunks derived from documents
  - query_history : past user queries and results
"""

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    source_type = Column(String(64), nullable=False)  # chatgpt | markdown | txt | pdf
    file_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 dedup
    title = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    status = Column(String(32), default="pending")  # pending | indexed | error
    error_message = Column(Text, nullable=True)

    chunks = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "source_type": self.source_type,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "error_message": self.error_message,
        }


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # position within document
    faiss_id = Column(Integer, nullable=True, index=True)  # row in FAISS index
    token_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, default=dict)  # extra metadata dict

    document = relationship("Document", back_populates="chunks")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "faiss_id": self.faiss_id,
            "token_count": self.token_count,
            "metadata": self.metadata_,
        }


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    sources = Column(JSON, default=list)       # list of source dicts
    similar_problems = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    duration_ms = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "query_text": self.query_text,
            "answer": self.answer,
            "sources": self.sources,
            "similar_problems": self.similar_problems,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_ms": self.duration_ms,
        }