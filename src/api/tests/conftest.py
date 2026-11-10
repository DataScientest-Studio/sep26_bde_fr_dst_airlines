import os
import sys
from pathlib import Path

# Doit être défini avant l'import de api.config (valeurs lues à l'import)
os.environ["API_KEY"] = "test-key"
os.environ.setdefault("PG_PASSWORD", "test")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient

from api.database import get_db
from api.main import app

HEADERS = {"X-API-Key": "test-key"}


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class FakeDB:
    """Session factice : enregistre les requêtes et renvoie des lignes prédéfinies."""

    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.calls = []
        self.committed = False

    def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params))
        if self.error:
            raise self.error
        return FakeResult(self.rows)

    def commit(self):
        self.committed = True


@pytest.fixture
def fake_db():
    return FakeDB()


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    # Pas de `with` : on évite le lifespan (chargement du modèle)
    yield TestClient(app, headers=HEADERS)
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    return TestClient(app)
