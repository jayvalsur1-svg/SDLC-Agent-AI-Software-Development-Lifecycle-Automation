"""Database operations for TaskBoard tasks.

The functions in this module own transaction boundaries: mutating operations
commit their changes and refresh returned ORM objects. They accept either the
Pydantic request models used by the API or plain mappings, keeping the CRUD
layer convenient to use from other application code as well.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate


def _payload_values(payload: TaskCreate | TaskUpdate | Mapping[str, Any]) -> dict[str, Any]:
    """Convert a schema or mapping to values suitable for a Task update.

    For ``TaskUpdate``, only explicitly supplied fields are returned so omitted
    properties remain unchanged. Unknown keys are discarded to prevent callers
    from assigning ORM internals or fields managed by the server.
    """
    if isinstance(payload, Mapping):
        values = dict(payload)
    elif hasattr(payload, "model_dump"):
        # Pydantic 2
        values = payload.model_dump(exclude_unset=True)
    elif hasattr(payload, "dict"):
        # Pydantic 1
        values = payload.dict(exclude_unset=True)
    else:
        raise TypeError("Task data must be a Pydantic model or mapping")

    allowed = {"title", "description", "due_date", "priority"}
    return {key: value for key, value in values.items() if key in allowed}


def create_task(db: Session, task_data: TaskCreate | Mapping[str, Any]) -> Task:
    """Create and return a task from validated request data."""
    task = Task(**_payload_values(task_data))
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise
    return task


def get_task(db: Session, task_id: int) -> Task | None:
    """Return the task with ``task_id``, or ``None`` when it does not exist."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    status: str | None = None,
    priority: str | None = None,
    *,
    completed: bool | None = None,
) -> list[Task]:
    """Return tasks, optionally filtered by completion status and priority.

    ``status`` accepts ``all``, ``active``, or ``completed`` (case-insensitively).
    The ``completed`` boolean is also available for callers that already use a
    boolean query parameter. If both are supplied, an inconsistent combination
    naturally yields no results.
    """
    query = db.query(Task)

    if status is not None:
        normalized_status = status.strip().lower()
        if normalized_status in {"", "all"}:
            pass
        elif normalized_status == "active":
            query = query.filter(Task.completed.is_(False))
        elif normalized_status == "completed":
            query = query.filter(Task.completed.is_(True))
        else:
            raise ValueError("status must be one of: all, active, completed")

    if completed is not None:
        query = query.filter(Task.completed.is_(completed))

    if priority is not None:
        normalized_priority = priority.strip().lower()
        if normalized_priority:
            priority_values = {"low": "Low", "medium": "Medium", "high": "High"}
            try:
                canonical_priority = priority_values[normalized_priority]
            except KeyError as exc:
                raise ValueError("priority must be one of: Low, Medium, High") from exc
            query = query.filter(Task.priority == canonical_priority)

    # Newer tasks appear first; the id tie-breaker makes ordering deterministic.
    return query.order_by(Task.created_at.desc(), Task.id.desc()).all()


def update_task(
    db: Session,
    task_or_id: Task | int,
    task_data: TaskUpdate | Mapping[str, Any],
) -> Task | None:
    """Apply the supplied fields to a task and return it.

    ``task_or_id`` may be an already-loaded ORM instance or a database id. The
    latter form returns ``None`` for a missing task, which lets route handlers
    produce a standard 404 response.
    """
    task = task_or_id if isinstance(task_or_id, Task) else get_task(db, task_or_id)
    if task is None:
        return None

    for field, value in _payload_values(task_data).items():
        setattr(task, field, value)

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise
    return task


def toggle_task(db: Session, task_or_id: Task | int) -> Task | None:
    """Invert a task's completion state and return the updated task."""
    task = task_or_id if isinstance(task_or_id, Task) else get_task(db, task_or_id)
    if task is None:
        return None

    task.completed = not task.completed
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise
    return task


def delete_task(db: Session, task_or_id: Task | int) -> Task | None:
    """Delete a task and return the deleted object, or ``None`` if not found."""
    task = task_or_id if isinstance(task_or_id, Task) else get_task(db, task_or_id)
    if task is None:
        return None

    try:
        db.delete(task)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return task
