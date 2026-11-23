"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Resolve paths from this file rather than the process working directory so the
# application can be started from any directory. The .env file lives at the
# project root alongside the application package.
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    """Parse a conventional environment-variable boolean value.

    Accepted true values are ``1``, ``true``, ``yes``, and ``on``; accepted
    false values are ``0``, ``false``, ``no``, and ``off`` (case-insensitive).
    Invalid values raise an error at startup rather than silently changing
    application behavior.
    """
    if value is None or not value.strip():
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        "DEBUG must be a boolean value (use true/false, yes/no, on/off, or 1/0)"
    )


# Keep the relative SQLite default compatible with a simple `uvicorn app.main:app`
# launch from the project root. DATABASE_URL can be replaced with a PostgreSQL
# URL without changes to the application code.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db").strip()
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./tasks.db"

DEBUG = _parse_bool(os.getenv("DEBUG"), default=False)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
