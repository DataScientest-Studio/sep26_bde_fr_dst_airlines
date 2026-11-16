"""Tests du collecteur AirLabs (airlabs.py). Aucun appel réseau ni GCS réel : tout est simulé."""
import csv
import json
import sys
from unittest.mock import MagicMock

import pytest
import requests

import airlabs


def fake_response(payload=None, ok=True, text="", status_error=None):
    """Construit une fausse réponse `requests`."""
    r = MagicMock()
    r.ok = ok
    r.text = text
    r.json.return_value = payload
    if status_error:
        r.raise_for_status.side_effect = status_error
    return r


def page(flights, has_more=False, total=None):
    """Une page de réponse AirLabs."""
    return {"response": flights, "request": {"has_more": has_more, "total_items": total}}


def make_airport(**overrides):
    item = {
        "desc": "schedules_to_cdg",
        "url": "https://airlabs.co/api/v9/schedules",
        "params": {"arr_iata": "CDG", "api_key": "{API_KEY}", "limit": 50},
        "pattern": "schedule_cdg_{TIMESTAMPH}.csv",
    }
    item.update(overrides)
    return airlabs.Airport(item)


# ---------------------------------------------------------------- get_api_key

KEYS = [{"name": "k1", "key": "AAA"}, {"name": "k2", "key": "BBB"}]
PING_OK = {"request": {"key": {"limits_total": 500}}}


def test_get_api_key_from_json_string(monkeypatch):
    """Les clés peuvent être passées en JSON brut (secret Cloud Run) : la première valide est retenue."""
    monkeypatch.setattr(requests, "get", lambda *a, **k: fake_response(PING_OK))
    assert airlabs.get_api_key(json.dumps(KEYS)) == ("k1", "AAA", 500)


def test_get_api_key_from_file(monkeypatch, tmp_path):
    """Les clés peuvent aussi venir d'un fichier JSON."""
    f = tmp_path / "keys.json"
    f.write_text(json.dumps(KEYS))
    monkeypatch.setattr(requests, "get", lambda *a, **k: fake_response(PING_OK))
    assert airlabs.get_api_key(str(f))[1] == "AAA"


def test_get_api_key_skips_expired_key(monkeypatch):
    """Une clé refusée (HTTP non ok) ou sans bloc 'request' est ignorée au profit de la suivante."""
    responses = [fake_response(ok=False, text="expired"), fake_response(PING_OK)]
    monkeypatch.setattr(requests, "get", lambda *a, **k: responses.pop(0))
    assert airlabs.get_api_key(json.dumps(KEYS)) == ("k2", "BBB", 500)


def test_get_api_key_none_available(monkeypatch):
    """Aucune clé utilisable : renvoie None."""
    monkeypatch.setattr(requests, "get", lambda *a, **k: fake_response({"error": "limit"}))
    assert airlabs.get_api_key(json.dumps(KEYS)) is None


# ------------------------------------------------------------- read_airports

def test_read_airports_injects_api_key(tmp_path):
    """Le marqueur {API_KEY} est remplacé dans les paramètres ; les valeurs non texte restent intactes."""
    f = tmp_path / "airports.json"
    f.write_text(json.dumps([{
        "desc": "d", "url": "u", "pattern": "p_{TIMESTAMP}.csv",
        "params": {"api_key": "{API_KEY}", "limit": 50},
    }]))
    airports = airlabs.read_airports("SECRET", str(f))
    assert airports[0].params == {"api_key": "SECRET", "limit": 50}


def test_real_airports_file_is_valid():
    """Le airports.json livré est lisible et chaque entrée a les champs requis."""
    path = airlabs.__file__.replace("airlabs.py", "airports.json")
    airports = airlabs.read_airports("K", path)
    assert airports
    for a in airports:
        assert a.params["api_key"] == "K"
        assert "{TIMESTAMP" in a.pattern


# --------------------------------------------------------------- collect_data

def test_collect_data_keeps_only_landed(monkeypatch):
    """Seuls les vols au statut 'landed' sont conservés."""
    flights = [{"flight": "A", "status": "landed"}, {"flight": "B", "status": "scheduled"}]
    monkeypatch.setattr(requests, "get", lambda *a, **k: fake_response(page(flights)))
    assert airlabs.collect_data(make_airport()) == [flights[0]]


def test_collect_data_paginates(monkeypatch):
    """Tant que has_more est vrai, la page suivante est demandée (offset = numéro de page)."""
    pages = [
        page([{"id": 1, "status": "landed"}], has_more=True),
        page([{"id": 2, "status": "landed"}], has_more=False),
    ]
    offsets = []

    def fake_get(url, params, timeout):
        offsets.append(params["offset"])
        return fake_response(pages.pop(0))

    monkeypatch.setattr(requests, "get", fake_get)
    data = airlabs.collect_data(make_airport())
    assert [d["id"] for d in data] == [1, 2]
    assert offsets == [0, 1]


def test_collect_data_stops_on_empty_page_with_has_more(monkeypatch):
    """Garde-fou anti boucle infinie : has_more vrai mais page vide => arrêt."""
    monkeypatch.setattr(requests, "get", lambda *a, **k: fake_response(page([], has_more=True)))
    assert airlabs.collect_data(make_airport()) == []


def test_collect_data_retries_then_succeeds(monkeypatch):
    """Une erreur réseau ponctuelle est retentée."""
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.ConnectionError("réseau")
        return fake_response(page([{"status": "landed"}]))

    monkeypatch.setattr(requests, "get", flaky)
    assert len(airlabs.collect_data(make_airport())) == 1
    assert calls["n"] == 2


def test_collect_data_raises_after_three_failures(monkeypatch):
    """1 appel + 2 retries : après 3 échecs l'exception remonte."""
    calls = {"n": 0}

    def always_fail(*a, **k):
        calls["n"] += 1
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "get", always_fail)
    with pytest.raises(requests.ConnectionError):
        airlabs.collect_data(make_airport())
    assert calls["n"] == 3


def test_collect_data_rejects_non_list_response(monkeypatch):
    """Un champ 'response' qui n'est pas une liste est une erreur explicite."""
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: fake_response({"response": {"error": "x"}, "request": {}})
    )
    with pytest.raises(ValueError):
        airlabs.collect_data(make_airport())


# ------------------------------------------------------------------- save_csv

def test_save_csv_no_rows_returns_no_path(tmp_path):
    """Sans données : aucun fichier, et un tuple (None, False) que run() peut dépiler."""
    assert airlabs.save_csv([], "x.csv", str(tmp_path)) == (None, False)
    assert not (tmp_path / "x.csv").exists()


def test_save_csv_writes_union_of_columns_and_json_for_nested(tmp_path):
    """Colonnes = union de toutes les lignes ; dict/list sérialisés en JSON."""
    rows = [{"a": 1, "nested": {"k": "é"}}, {"a": 2, "b": [1, 2]}]
    path, istemp = airlabs.save_csv(rows, "out.csv", str(tmp_path))
    assert istemp is False
    with open(path, newline="", encoding="utf-8-sig") as f:
        out = list(csv.DictReader(f))
    assert list(out[0].keys()) == ["a", "nested", "b"]
    assert json.loads(out[0]["nested"]) == {"k": "é"}
    assert json.loads(out[1]["b"]) == [1, 2]


def test_save_csv_appends_without_duplicate_header(tmp_path):
    """Un second appel sur le même fichier ajoute des lignes sans répéter l'en-tête."""
    airlabs.save_csv([{"a": 1}], "out.csv", str(tmp_path))
    airlabs.save_csv([{"a": 2}], "out.csv", str(tmp_path))
    lines = (tmp_path / "out.csv").read_text(encoding="utf-8-sig").splitlines()
    assert lines == ["a", "1", "2"]


def test_save_csv_without_folder_uses_temp_file():
    """Sans dossier local : fichier temporaire, signalé par istemp=True."""
    import os

    path, istemp = airlabs.save_csv([{"a": 1}], "ignored.csv", None)
    try:
        assert istemp is True and os.path.isfile(path)
    finally:
        os.remove(path)


# ------------------------------------------------------------------------ run

@pytest.fixture
def run_env(monkeypatch, tmp_path):
    """Environnement de run() : clé valide, un fichier d'aéroports, collecte et GCS simulés."""
    airports_file = tmp_path / "airports.json"
    airports_file.write_text(json.dumps([
        {"desc": "cdg", "url": "u", "params": {"api_key": "{API_KEY}"}, "pattern": "cdg_{TIMESTAMP}.csv"},
        {"desc": "ory", "url": "u", "params": {"api_key": "{API_KEY}"}, "pattern": "ory_{TIMESTAMP}.csv"},
    ]))
    monkeypatch.setattr(airlabs, "get_api_key", lambda keys: ("k1", "SECRET", 100))
    uploads = []
    monkeypatch.setattr(airlabs, "uploader_gcs", lambda *a: uploads.append(a))
    return {"airports": str(airports_file), "uploads": uploads, "tmp": tmp_path, "mp": monkeypatch}


def test_run_without_valid_key_raises(monkeypatch):
    """Régression : avant, run() plantait sur None[1] ; maintenant une erreur explicite."""
    monkeypatch.setattr(airlabs, "get_api_key", lambda keys: None)
    with pytest.raises(RuntimeError):
        airlabs.run("[]", "airports.json")


def test_run_rejects_bad_bucket_path(run_env):
    """Un chemin de bucket sans '/' est refusé."""
    with pytest.raises(Exception, match="Bad Bucket"):
        airlabs.run("[]", run_env["airports"], bucket_path="pas-de-slash")


def test_run_uploads_each_airport_to_bucket(run_env):
    """Chaque aéroport ayant des données est envoyé vers gs://bucket/chemin/fichier."""
    run_env["mp"].setattr(airlabs, "collect_data", lambda airport: [{"a": 1}])
    airlabs.run("[]", run_env["airports"], bucket_path="mon-bucket/raw/airlabs/")
    blobs = [u[2] for u in run_env["uploads"]]
    assert len(blobs) == 2
    assert all(b.startswith("raw/airlabs/") for b in blobs)
    assert run_env["uploads"][0][1] == "mon-bucket"


def test_run_removes_temp_file_after_upload(run_env):
    """Sans dossier local, le fichier temporaire est supprimé après l'envoi."""
    import os

    run_env["mp"].setattr(airlabs, "collect_data", lambda airport: [{"a": 1}])
    airlabs.run("[]", run_env["airports"], bucket_path="b/p")
    for upload in run_env["uploads"]:
        assert not os.path.exists(upload[0])


def test_run_continues_after_one_airport_fails(run_env):
    """Une erreur sur un aéroport ne bloque pas les suivants."""
    def collect(airport):
        if airport.desc == "cdg":
            raise RuntimeError("API down")
        return [{"a": 1}]

    run_env["mp"].setattr(airlabs, "collect_data", collect)
    airlabs.run("[]", run_env["airports"], bucket_path="b/p")
    assert len(run_env["uploads"]) == 1  # seul ory a été envoyé


def test_run_with_no_flights_does_not_upload(run_env):
    """Régression : sans vol atterri, save_csv renvoyait None et run() levait un TypeError."""
    run_env["mp"].setattr(airlabs, "collect_data", lambda airport: [])
    airlabs.run("[]", run_env["airports"], bucket_path="b/p")
    assert run_env["uploads"] == []


def test_run_local_dir_without_bucket(run_env):
    """Avec --dir et sans bucket, les CSV sont écrits localement et rien n'est envoyé."""
    run_env["mp"].setattr(airlabs, "collect_data", lambda airport: [{"a": 1}])
    out = run_env["tmp"] / "out"
    airlabs.run("[]", run_env["airports"], local_dir=str(out))
    assert len(list(out.glob("*.csv"))) == 2
    assert run_env["uploads"] == []


# ----------------------------------------------------------------------- main

def test_main_passes_google_credentials(monkeypatch):
    """Régression : main() lisait args.google_creds (inexistant) au lieu de args.google_cred."""
    captured = {}
    monkeypatch.setattr(airlabs, "run", lambda *a: captured.setdefault("args", a))
    monkeypatch.setattr(sys, "argv", [
        "airlabs.py", "--api-keys-file", "k.json", "--airports", "a.json",
        "--bucket-path", "b/p", "--google-credentials", "cred.json",
    ])
    airlabs.main()
    assert captured["args"] == ("k.json", "a.json", "b/p", None, "cred.json")
