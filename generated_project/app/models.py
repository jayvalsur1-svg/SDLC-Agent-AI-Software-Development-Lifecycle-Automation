"""SQLAlchemy ORM models for TaskBoard."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    text,
)

from app.db import Base


class Task(Base):
    """A task tracked on the board.

    ``due_date`` is a calendar date rather than a timestamp because the UI asks
    for a date without a time of day. Creation and update timestamps are stored
    separately and populated in UTC.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High')",
            name="ck_tasks_priority",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    priority = Column(
        String(10),
        nullable=False,
        default="Medium",
        server_default=text("'Medium'"),
    )
    completed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id!r} title={self.title!r} "
            f"completed={self.completed!r}>"
        )
