"""Tests for the worker health mechanism."""

from fastapi.testclient import TestClient

from worker.main import app, settings


def test_health_returns_worker_identity() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "api-sfp-workers",
        "environment": settings.app_env,
        "version": "0.1.0",
    }
