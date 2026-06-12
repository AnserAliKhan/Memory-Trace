"""
Database engine, session factory, and init helper.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
from config import get_settings


def _make_engine():
    cfg = get_settings()
    connect_args = {}
    if cfg.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(
        cfg.database_url,
        connect_args=connect_args,
        echo=False,
    )


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()