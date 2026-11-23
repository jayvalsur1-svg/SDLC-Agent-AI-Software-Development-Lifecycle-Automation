"""REST API endpoints for creating and managing TaskBoard tasks."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.db import get_db
from app.schemas import TaskCreate, TaskRead, TaskUpdate


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead], summary="List tasks")
def list_tasks(
    status_filter: Literal["all", "active", "completed"] = Query(
        default="all",
        alias="status",
        description="Filter by completion status.",
    ),
    priority: Literal["Low", "Medium", "High"] | None = Query(
        default=None,
        description="Optionally filter by priority.",
    ),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    """Return tasks, optionally filtered by completion status and priority."""
    return crud.get_tasks(db, status=status_filter, priority=priority)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)) -> TaskRead:
    """Validate and persist a new task."""
    return crud.create_task(db, task_data)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Retrieve a task",
)
def retrieve_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    """Return one task, or a JSON 404 response when it does not exist."""
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return task


def _update_task(task_id: int, task_data: TaskUpdate, db: Session) -> TaskRead:
    """Shared partial-update implementation used by PATCH and PUT."""
    task = crud.update_task(db, task_id, task_data)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task fields",
)
def patch_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskRead:
    """Update only the supplied fields, leaving all other fields unchanged."""
    return _update_task(task_id, task_data, db)


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task fields",
    include_in_schema=False,
)
def put_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskRead:
    """Accept PUT clients using the same safe partial-update payload as PATCH."""
    return _update_task(task_id, task_data, db)


@router.post(
    "/{task_id}/toggle",
    response_model=TaskRead,
    summary="Toggle task completion",
)
def toggle_task(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    """Invert and return a task's completion status."""
    task = crud.toggle_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a task",
)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete a task and return an empty 204 response."""
    task = crud.delete_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
