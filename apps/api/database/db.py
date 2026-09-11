"""
Single source of truth for the SQLAlchemy engine and session factory.

This replaces the old, duplicated `database/connection.py` +
`database/client.py` pair (flagged as duplication in the pre-migration
Flask app's AUDIT.md, M-3) with one engine, one session factory, one
`get_session()` context manager, and one FastAPI dependency.

Works against both:
  - a local SQLite file (default, for zero-setup local dev), and
  - a Neon Postgres pooled connection string (production) — set
    DATABASE_URL to something like:
    postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/dbname?sslmode=require

Schema is managed by Alembic (see alembic/), not by
`Base.metadata.create_all()` — that call is only used by the test suite's
in-memory SQLite fixtures, never against a real database.
"""
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import NullPool

from config.settings import settings
from database.models import Base
import models.prediction  # noqa: F401 — registers Prediction/SessionData/PredictionMetadata on Base.metadata; see the identical fix in alembic/env.py

logger = logging.getLogger(__name__)


def _make_engine():
    url = settings.DATABASE_URL
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}

    if url.startswith("sqlite"):
        # Needed so the same connection can be used across the request/
        # response cycle in a single-threaded test/dev server.
        connect_args["check_same_thread"] = False
    else:
        # Neon's pooled ("-pooler") endpoint already does connection
        # pooling via PgBouncer in front of Postgres. Layering SQLAlchemy's
        # own pool on top of that (the default in a long-lived process)
        # is fine locally, but inside a short-lived serverless function
        # NullPool — a fresh connection per checkout, no idle pool to leak
        # across invocations — is the safer default.
        import os
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            engine_kwargs["poolclass"] = NullPool
        else:
            engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
            engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
            engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT
            engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE

    return create_engine(url, connect_args=connect_args, echo=settings.DEBUG, **engine_kwargs)


engine = _make_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def create_all_for_tests():
    """Create tables directly from the models — test fixtures only. Real
    deployments run `alembic upgrade head` instead."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context-manager session for use outside of a FastAPI request
    (scripts, apps/ingest, engine/* callers that pre-date the API layer)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: `db: Session = Depends(get_db)`."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def verify_connection() -> bool:
    """Cheap health check — used by routers/health.py and routers/status.py."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
