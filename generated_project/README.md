# TaskBoard

TaskBoard is a lightweight task manager built with **FastAPI**, **SQLAlchemy**, **SQLite**, **Jinja2**, and vanilla JavaScript. It provides a server-rendered task board and a JSON REST API for creating, listing, editing, completing, and deleting tasks. The browser updates the board through the Fetch API without full-page reloads.

## Features

- Create tasks with a required title, optional description and due date, and Low/Medium/High priority.
- Filter tasks by completion status and priority.
- Edit task fields in place, toggle completion, or delete tasks.
- Interactive Swagger UI and OpenAPI schema.
- Configure `DATABASE_URL` to use SQLite by default or another SQLAlchemy-supported database such as PostgreSQL.

## Requirements and startup

Python 3.10 or newer and pip are required. From the project root:

```bash
python -m venv .venv
# Activate the environment (Windows: .venv\\Scripts\\Activate.ps1; macOS/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> for the task board, <http://127.0.0.1:8000/docs> for Swagger UI, or <http://127.0.0.1:8000/redoc> for ReDoc. The application creates missing database tables on startup. With the defaults, SQLite stores data in `tasks.db` in the current working directory.

## Configuration

Copy `.env.example` to `.env` in the project root and edit the values as needed:

```dotenv
DATABASE_URL=sqlite:///./tasks.db
DEBUG=false
SECRET_KEY=replace-this-with-a-long-random-secret
```

The application loads `.env` automatically, and process environment variables can also be used. A PostgreSQL URL can be configured, for example, as `postgresql+psycopg://taskboard:password@localhost:5432/taskboard`; install the corresponding SQLAlchemy driver separately. `DEBUG` accepts common true/false values and defaults to false. `SECRET_KEY` is currently a configuration placeholder; set a strong secret before deployment. Do not commit `.env` files or production credentials.

## Web interface

The board at `/` renders the current tasks and then uses JavaScript for interactive operations. It supports adding tasks, filtering, editing all task fields, toggling completion, and deleting tasks. Empty descriptions and due dates are allowed. Task titles are trimmed and must contain between 1 and 200 characters.

## REST API

All task endpoints are under `/api/tasks`. Request and response bodies use JSON, except successful deletion, which returns an empty `204 No Content`. Dates use the ISO `YYYY-MM-DD` format and priorities are case-sensitive (`Low`, `Medium`, or `High`).

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/tasks` | List tasks, optionally filtered by status and priority |
| `POST` | `/api/tasks` | Create a task (`201 Created`) |
| `GET` | `/api/tasks/{task_id}` | Retrieve one task |
| `PATCH` | `/api/tasks/{task_id}` | Partially update supplied task fields |
| `POST` | `/api/tasks/{task_id}/toggle` | Toggle completion and return the updated task |
| `DELETE` | `/api/tasks/{task_id}` | Delete a task (`204 No Content`) |

The list endpoint accepts `status=all`, `status=active`, or `status=completed`, and an optional priority filter. For example: `GET /api/tasks?status=active&priority=High`. Omit filters to list all tasks. Set `description` or `due_date` to `null` in a PATCH request to clear the value. Missing tasks return JSON `404` responses; invalid request data and filter values return FastAPI's JSON `422` validation response.

## Database and migrations

Set `DATABASE_URL` to switch database backends. A PostgreSQL deployment must install a compatible driver such as `psycopg`. Tables are created if missing at application startup; `create_all()` does not alter existing tables. Alembic is included for migrations; run its commands from the project root, for example:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

There are currently no migration revisions in `alembic/versions`; create and review a migration when making schema changes to an existing database.

## Tests

Install development/test dependencies and run the functional API/UI test suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use a fresh in-memory SQLite database and exercise the app lifespan, rendered board, Swagger/OpenAPI, CRUD operations, filters, validation, and 404 responses.
