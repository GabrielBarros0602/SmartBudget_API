"""Smoke test: proves the app boots and the liveness endpoint answers."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_exposes_version_and_environment(client: TestClient) -> None:
    body = client.get("/health").json()

    assert "version" in body
    assert "environment" in body
