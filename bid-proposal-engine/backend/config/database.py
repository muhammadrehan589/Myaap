"""Database configuration — SQLAlchemy engine, session, and base model.

Supports both PostgreSQL (with pgvector) and SQLite (fallback).
Connection string is read from DATABASE_URL environment variable.
If not set, defaults to SQLite at backend/data/bidengine.db.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Resolve database path relative to this file
# config/database.py -> config -> backend -> data/bidengine.db
_config_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_config_dir)
_db_path = os.path.join(_backend_dir, "data", "bidengine.db")

# Database URL from environment, fallback to SQLite with absolute path
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")

# Engine configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    IS_POSTGRES = False
else:
    # PostgreSQL-specific settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )
    IS_POSTGRES = True

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined by ORM models."""
    from models import bid_history, capability_library, user, proposal, requirement, compliance
    Base.metadata.create_all(bind=engine)


def enable_pgvector():
    """Enable pgvector extension (PostgreSQL only)."""
    if IS_POSTGRES:
        with engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        return True
    return False
