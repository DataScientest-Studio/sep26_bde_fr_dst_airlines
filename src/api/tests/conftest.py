"""Fixtures partagées par les tests de l'API.

Aucune vraie base de données n'est utilisée : la dépendance `get_db` de FastAPI
est remplacée par une fausse session (FakeDB) qui enregistre les requêtes.
"""
import os
import sys
from pathlib import Path

# Doit être défini avant l'import de api.config (valeurs lues à l'import)
os.environ["API_KEY"] = "test-key"
os.environ.setdefault("PG_PASSWORD", "test")

# Permet d'importer le paquet `api` quel que soit le dossier de lancement de pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient

from api.database import get_db
from api.main import app

# En-tête d'authentification valide pour les tests
HEADERS = {"X-API-Key": "test-key"}


class FakeResult:
    """Imite le résultat SQLAlchemy : .mappings().all() et .first()."""

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
        self.rows = rows or []      # lignes renvoyées par execute()
        self.error = error          # si défini, execute() lève cette exception
        self.calls = []             # historique : liste de (requête SQL, paramètres)
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
    """Fausse session de base de données, configurable dans chaque test."""
    return FakeDB()


@pytest.fixture
def client(fake_db):
    """Client HTTP authentifié, branché sur la fausse base."""
    app.dependency_overrides[get_db] = lambda: fake_db
    # Pas de `with` : on évite le lifespan (chargement du modèle)
    yield TestClient(app, headers=HEADERS)
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client():
    """Client HTTP sans clé API, pour tester les refus d'accès."""
    return TestClient(app)
