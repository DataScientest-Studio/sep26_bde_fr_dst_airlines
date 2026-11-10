from fastapi.testclient import TestClient

from api.config import settings
from api.main import app


def test_missing_key_is_rejected(anon_client):
    assert anon_client.get("/airlines").status_code == 403


def test_wrong_key_is_rejected(anon_client):
    r = anon_client.get("/airlines", headers={"X-API-Key": "nope"})
    assert r.status_code == 403


def test_valid_key_is_accepted(client):
    assert client.get("/airlines").status_code == 200


def test_empty_server_key_refuses_everything(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")
    c = TestClient(app)
    assert c.get("/airlines", headers={"X-API-Key": ""}).status_code == 403


def test_cors_not_open_to_all_origins(client):
    r = client.options(
        "/airlines",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin") != "*"
