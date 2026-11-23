"""Alembic migration environment for TaskBoard.

The application and migration runner share the database URL and SQLAlchemy
metadata defined by the ``app`` package. This keeps migrations consistent with
the engine configuration used by the API (including SQLite-specific options).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

from app.config import DATABASE_URL
from app.db import engine
from app.db import Base
from app import models  # noqa: F401 -- registers ORM tables on Base.metadata


# Alembic's ConfigParser treats percent signs as interpolation markers. Escape
# them when writing the URL so credentials containing '%' are preserved.
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Importing app.models above is essential: it registers Task and its table on
# this metadata object before autogeneration or migration execution begins.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a DBAPI connection."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_with_connection(connection: Connection) -> None:
    """Configure Alembic and execute migrations on an open connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the application's configured SQLAlchemy engine."""
    with engine.connect() as connection:
        _run_with_connection(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
