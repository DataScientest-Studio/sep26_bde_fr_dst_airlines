"""Configuration pytest : rend le module `airlabs` importable depuis la racine du dépôt
(la CI lance `pytest src/airlabs_collect/tests`) et supprime les attentes réelles."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Les retries et la pagination attendent 10 s : on neutralise time.sleep."""
    monkeypatch.setattr("time.sleep", lambda *_: None)
