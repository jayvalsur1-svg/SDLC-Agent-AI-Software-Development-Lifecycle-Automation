"""Pydantic schemas for TaskBoard API requests and responses.

The models support both Pydantic 1.x and 2.x, allowing ORM instances to be
serialized without requiring route handlers to convert them to dictionaries.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import pydantic
from pydantic import BaseModel, constr


_PYDANTIC_V2 = int(pydantic.VERSION.split(".", maxsplit=1)[0]) >= 2
if _PYDANTIC_V2:
    from pydantic import ConfigDict, field_validator
else:
    from pydantic import validator


TaskPriority = Literal["Low", "Medium", "High"]
TaskTitle = constr(strip_whitespace=True, min_length=1, max_length=200)


class TaskCreate(BaseModel):
    """Fields accepted when creating a task."""

    title: TaskTitle
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority = "Medium"


class TaskUpdate(BaseModel):
    """Partial task update.

    Omitted fields are left unchanged by the CRUD layer. Description and due
    date may explicitly be set to ``null`` to clear them; title may not.
    Completion is intentionally changed through the dedicated toggle route.
    """

    title: TaskTitle | None = None
    description: str | None = None
    due_date: date | None = None
    priority: TaskPriority | None = None

    if _PYDANTIC_V2:

        @field_validator("title", mode="before")
        @classmethod
        def title_must_not_be_null(cls, value: object) -> object:
            if value is None:
                raise ValueError("title may not be null")
            return value
    else:

        @validator("title", pre=True)
        def title_must_not_be_null(cls, value: object) -> object:
            if value is None:
                raise ValueError("title may not be null")
            return value


class TaskRead(BaseModel):
    """Task representation returned by the API and supplied to templates."""

    id: int
    title: str
    description: str | None
    due_date: date | None
    priority: TaskPriority
    completed: bool
    created_at: datetime
    updated_at: datetime

    if _PYDANTIC_V2:
        model_config = ConfigDict(from_attributes=True)
    else:

        class Config:
            orm_mode = True
