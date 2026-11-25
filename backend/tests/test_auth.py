from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_basic_auth_can_protect_the_app(monkeypatch):
    monkeypatch.setattr(settings, "require_auth", True)
    monkeypatch.setattr(settings, "app_username", "demo")
    monkeypatch.setattr(settings, "app_password", "strong-password")
    client = TestClient(app)

    assert client.get("/api/copilot/status").status_code == 401
    response = client.get("/api/copilot/status", auth=("demo", "strong-password"))
    assert response.status_code == 200


def test_auth_fails_closed_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "require_auth", True)
    monkeypatch.setattr(settings, "app_username", "")
    monkeypatch.setattr(settings, "app_password", "")

    assert TestClient(app).get("/api/copilot/status").status_code == 503
