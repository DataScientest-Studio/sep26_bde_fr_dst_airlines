"""Tests de l'authentification par clé API (header X-API-Key) et du CORS."""
from fastapi.testclient import TestClient

from api.config import settings
from api.main import app


def test_missing_key_is_rejected(anon_client):
    """Sans en-tête X-API-Key : 403."""
    assert anon_client.get("/airlines").status_code == 403


def test_wrong_key_is_rejected(anon_client):
    """Avec une mauvaise clé : 403."""
    r = anon_client.get("/airlines", headers={"X-API-Key": "nope"})
    assert r.status_code == 403


def test_valid_key_is_accepted(client):
    """Avec la bonne clé : l'endpoint répond normalement."""
    assert client.get("/airlines").status_code == 200


def test_empty_server_key_refuses_everything(monkeypatch):
    """Si API_KEY n'est pas configurée côté serveur, tout accès est refusé
    (même avec une clé vide), au lieu de laisser l'API ouverte."""
    monkeypatch.setattr(settings, "API_KEY", "")
    c = TestClient(app)
    assert c.get("/airlines", headers={"X-API-Key": ""}).status_code == 403


def test_cors_not_open_to_all_origins(client):
    """Une origine inconnue ne doit pas recevoir `Access-Control-Allow-Origin: *`."""
    r = client.options(
        "/airlines",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers.get("access-control-allow-origin") != "*"
