"""FastAPI application entry point for TaskBoard."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models  # Ensure ORM mappings are registered with Base.metadata.
from app.crud import get_tasks
from app.db import Base, engine, get_db
from app.routers.tasks import router as tasks_router


APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create missing tables at startup; use migrations for schema changes."""
    # The explicit import above ensures every model is included in the metadata.
    _ = models
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskBoard",
    description="A lightweight task manager with a server-rendered UI and REST API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(tasks_router)


@app.get("/", include_in_schema=False)
def index(request: Request, db: Session = Depends(get_db)):
    """Render the task board with the current tasks."""
    tasks = get_tasks(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"tasks": tasks},
    )
