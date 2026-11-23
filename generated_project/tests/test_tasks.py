"""Functional tests for the TaskBoard API and server-rendered interface."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.db import Base, get_db
from app.main import app
from app import models  # noqa: F401 -- register model metadata


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Use a fresh in-memory SQLite database for each test, including lifespan."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(main_module, "engine", engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create(client: TestClient, **overrides: object) -> dict:
    payload = {"title": "  Write tests  "}
    payload.update(overrides)
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_board_page_and_swagger_are_available(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "TaskBoard" in page.text
    assert "task-form" in page.text

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "Swagger UI" in docs.text
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/api/tasks" in schema.json()["paths"]


def test_create_defaults_retrieve_and_delete(client: TestClient) -> None:
    task = create(client)
    assert task["title"] == "Write tests"
    assert task["description"] is None
    assert task["due_date"] is None
    assert task["priority"] == "Medium"
    assert task["completed"] is False

    retrieved = client.get(f"/api/tasks/{task['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json() == task

    deleted = client.delete(f"/api/tasks/{task['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/tasks/{task['id']}").status_code == 404


def test_create_and_partial_update_all_editable_fields(client: TestClient) -> None:
    task = create(
        client,
        description="initial note",
        due_date="2026-12-15",
        priority="High",
    )
    response = client.patch(
        f"/api/tasks/{task['id']}",
        json={"title": " Revised ", "description": None, "due_date": None},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["title"] == "Revised"
    assert updated["description"] is None
    assert updated["due_date"] is None
    assert updated["priority"] == "High"
    assert updated["completed"] is False

    priority_update = client.patch(f"/api/tasks/{task['id']}", json={"priority": "Low"})
    assert priority_update.status_code == 200
    assert priority_update.json()["priority"] == "Low"


def test_toggle_is_dedicated_and_reversible(client: TestClient) -> None:
    task = create(client)
    first = client.post(f"/api/tasks/{task['id']}/toggle")
    assert first.status_code == 200
    assert first.json()["completed"] is True
    second = client.post(f"/api/tasks/{task['id']}/toggle")
    assert second.status_code == 200
    assert second.json()["completed"] is False


def test_status_and_priority_filters(client: TestClient) -> None:
    low = create(client, title="Low active", priority="Low")
    high = create(client, title="High done", priority="High")
    medium = create(client, title="Medium active", priority="Medium")
    client.post(f"/api/tasks/{high['id']}/toggle")

    assert len(client.get("/api/tasks").json()) == 3
    assert [t["id"] for t in client.get("/api/tasks?status=active").json()] == [medium["id"], low["id"]]
    assert [t["id"] for t in client.get("/api/tasks?status=completed").json()] == [high["id"]]
    assert [t["id"] for t in client.get("/api/tasks?priority=High").json()] == [high["id"]]
    assert [t["id"] for t in client.get("/api/tasks?status=active&priority=Low").json()] == [low["id"]]


def test_validation_errors_are_422_json(client: TestClient) -> None:
    invalid_payloads = [
        {},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "valid", "priority": "Urgent"},
        {"title": "valid", "due_date": "not-a-date"},
    ]
    for payload in invalid_payloads:
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/json")
        assert isinstance(response.json().get("detail"), list)

    task = create(client)
    for payload in ({"title": None}, {"title": " "}, {"priority": "urgent"}):
        response = client.patch(f"/api/tasks/{task['id']}", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()

    assert client.get("/api/tasks?status=archived").status_code == 422
    assert client.get("/api/tasks?priority=Urgent").status_code == 422


def test_missing_task_mutations_and_reads_return_json_404(client: TestClient) -> None:
    for response in (
        client.get("/api/tasks/999"),
        client.patch("/api/tasks/999", json={"title": "Missing"}),
        client.post("/api/tasks/999/toggle"),
        client.delete("/api/tasks/999"),
    ):
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/json")
        assert "detail" in response.json()


def test_list_is_ordered_newest_first(client: TestClient) -> None:
    first = create(client, title="First")
    second = create(client, title="Second")
    assert [item["id"] for item in client.get("/api/tasks").json()] == [second["id"], first["id"]]
