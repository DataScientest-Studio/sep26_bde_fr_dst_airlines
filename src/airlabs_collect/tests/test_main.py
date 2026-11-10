"""Tests du point d'entrée HTTP (Cloud Run / Cloud Scheduler)."""
import pytest

# functions_framework est dans requirements.txt ; on saute le test s'il n'est pas installé localement
pytest.importorskip("functions_framework")

import main  # noqa: E402


def test_run_http_calls_run_with_env(monkeypatch):
    """Le handler lit AIRLABS_API_KEYS dans l'environnement et lance la collecte."""
    monkeypatch.setenv("AIRLABS_API_KEYS", '[{"name": "k", "key": "x"}]')
    captured = {}
    monkeypatch.setattr(main, "run", lambda *a: captured.setdefault("args", a))
    # functions_framework.http renvoie la fonction d'origine, appelable directement
    assert main.run_http(request=None) == ("OK", 200)
    assert captured["args"][0] == '[{"name": "k", "key": "x"}]'
    assert captured["args"][1] == main.AIRPORTS_FILE


def test_run_http_fails_without_api_keys(monkeypatch):
    """Sans secret AIRLABS_API_KEYS, le handler échoue (KeyError) au lieu de collecter."""
    monkeypatch.delenv("AIRLABS_API_KEYS", raising=False)
    with pytest.raises(KeyError):
        main.run_http(request=None)
