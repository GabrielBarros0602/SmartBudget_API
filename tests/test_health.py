"""Health probes: the app boots, liveness never depends on the database, readiness does."""

from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import create_app


def _client_with_session(session: Session) -> TestClient:
    """A client whose requests get `session` instead of a real database session."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app)


def _unreachable_database() -> Mock:
    session = Mock(spec=Session)
    session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("connection refused"))
    return session


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_exposes_version_and_environment(client: TestClient) -> None:
    body = client.get("/health").json()

    assert "version" in body
    assert "environment" in body


def test_health_stays_ok_when_the_database_is_down() -> None:
    response = _client_with_session(_unreachable_database()).get("/health")

    assert response.status_code == 200


def test_ready_returns_ok_when_the_database_answers() -> None:
    session = Mock(spec=Session)

    response = _client_with_session(session).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    session.execute.assert_called_once()


def test_ready_returns_503_when_the_database_is_down() -> None:
    response = _client_with_session(_unreachable_database()).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
