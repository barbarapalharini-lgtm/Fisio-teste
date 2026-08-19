from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

SQLITE_URL = "sqlite:///sistema_fisio.db"

engine = create_engine(SQLITE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db(engine_to_use=None) -> None:
    """Create database tables for the application.

    If an engine is provided, use it for initialization. This is useful for
    tests that want an in-memory SQLite database.
    """
    from .models import Base

    Base.metadata.create_all(bind=engine_to_use or engine)
