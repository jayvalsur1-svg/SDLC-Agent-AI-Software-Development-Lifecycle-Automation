"""SQLAlchemy engine, session factory, and request-scoped dependency."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL


# Parse the URL once so SQLite-specific engine options can be applied without
# affecting PostgreSQL (or other supported SQLAlchemy backends).
_database_url = make_url(DATABASE_URL)
_engine_options: dict[str, object] = {"pool_pre_ping": True}

if _database_url.drivername.startswith("sqlite"):
    # SQLite connections are not inherently thread-safe. FastAPI can serve a
    # request on a different worker thread from the one that opened a connection.
    _engine_options["connect_args"] = {"check_same_thread": False}

    # Ensure file-backed databases can start when their parent directory does
    # not yet exist. Do not interpret SQLite URI filenames as ordinary paths.
    _sqlite_uri = str(_database_url.query.get("uri", "")).lower() in {
        "1",
        "true",
        "yes",
    }
    _database_name = _database_url.database
    _is_memory_database = _database_name in (None, "", ":memory:") or (
        _sqlite_uri and "mode=memory" in str(_database_name).lower()
    )

    if _database_name and not _is_memory_database and not _sqlite_uri:
        Path(_database_name).expanduser().resolve().parent.mkdir(
            parents=True, exist_ok=True
        )

    # Share one in-memory database across threads, which is especially useful
    # for FastAPI's threaded test clients.
    if _is_memory_database:
        _engine_options["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_options)

# Keep ORM instances usable after commits and avoid implicit flushes until a
# transaction is explicitly committed by the CRUD layer.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a request and always release its connection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
