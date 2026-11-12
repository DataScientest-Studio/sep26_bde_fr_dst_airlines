"""Tests des endpoints de prédiction et de déploiement de modèle.

Le modèle ML et l'appel météo (Open-Meteo) sont simulés : aucun test
n'utilise le réseau ni un vrai fichier joblib.
"""
import numpy as np
import pytest

from api.ml_model import ml_manager

# Vol minimal valide pour /predict (seuls les champs utiles au modèle sont fournis)
FLIGHT = {
    "flight": {
        "airline_icao": "AFR", "dep_icao": "LFPG", "arr_icao": "LFMN",
        "flight_date": "2026-11-10", "dep_time": "09:00", "arr_time": "10:30",
        "dep_lat": "49.01", "dep_lng": "2.55",
        "arr_lat": "43.65", "arr_lng": "7.21",
    }
}

# Réponse météo factice, avec toutes les variables attendues par build_features
WEATHER = {
    "temperature_2m": 10, "dew_point_2m": 5, "relative_humidity_2m": 70, "pressure_msl": 1010,
    "cloud_cover": 50, "cloud_cover_low": 10, "cloud_cover_mid": 20, "cloud_cover_high": 30,
    "wind_speed_10m": 12, "wind_direction_10m": 90, "wind_gusts_10m": 20,
    "precipitation": 0, "snowfall": 0, "weather_code": 1,
}

# Météo factice au départ : valeurs différentes pour vérifier que arr_* et dep_* ne sont pas mélangés
DEP_WEATHER = {**WEATHER, "temperature_2m": 4, "dew_point_2m": 1}


class DummyModel:
    """Faux modèle Scikit-Learn : prédit toujours 20 min de retard, probabilité 0.7."""

    def predict(self, df):
        return [20.0] * len(df)

    def predict_proba(self, df):
        # Colonne 0 = pas de retard, colonne 1 = retard
        return np.array([[0.3, 0.7]] * len(df))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Remplace les appels Open-Meteo (arrivée et départ) par des données fixes (appliqué à tous les tests)."""
    monkeypatch.setattr("api.ml_model.get_weather", lambda *a, **k: WEATHER)
    monkeypatch.setattr("api.ml_model.get_dep_weather", lambda *a, **k: DEP_WEATHER)


def test_predict_without_model_is_503(client, monkeypatch):
    """Sans modèle chargé, l'API doit répondre 503 (service indisponible)."""
    monkeypatch.setattr(ml_manager, "model", None)
    assert client.post("/predict", json=FLIGHT).status_code == 503


def test_predict_single(client, monkeypatch):
    """Prédiction d'un vol : retard détecté car probabilité (0.7) >= 0.5."""
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict", json=FLIGHT)
    assert r.status_code == 200
    body = r.json()
    assert body["is_delayed"] is True
    assert body["delay_probability"] == pytest.approx(0.7)


def test_predict_batch(client, monkeypatch):
    """Un lot de 2 vols renvoie 2 prédictions."""
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict-batch", json={"flights": [FLIGHT, FLIGHT]})
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 2


def test_predict_empty_batch(client, monkeypatch):
    """Un lot vide renvoie une liste vide, sans erreur."""
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict-batch", json={"flights": []})
    assert r.json() == {"predictions": []}


def test_build_features_columns():
    """build_features produit les colonnes attendues par le modèle (marts.mrt_ml_flights_features)."""
    from api.flight_predictor import build_features

    row = build_features({**FLIGHT["flight"]}, WEATHER, DEP_WEATHER)
    assert row["adep"] == "LFPG" and row["ades"] == "LFMN"
    assert row["arr_hour_local"] == 10
    assert row["dow"] == 2  # 2026-11-10 est un mardi (isoweekday : lundi = 1)
    assert row["arr_temp_dew_spread"] == 5  # température arrivée (10) - point de rosée (5)
    assert row["dep_temperature_2m"] == 4
    assert row["dep_temp_dew_spread"] == 3  # température départ (4) - point de rosée (1)


@pytest.mark.parametrize("name", ["a b", "x;drop", "..%2Fetc"])
def test_deploy_rejects_bad_names(client, name):
    """Les noms de modèle avec caractères interdits sont refusés (anti path traversal)."""
    assert client.post(f"/models/{name}/deploy").status_code in (404, 422)


def test_deploy_unknown_model_is_404(client, fake_db):
    """Un modèle absent de ml.model_runs renvoie 404."""
    fake_db.rows = []  # la requête SELECT ne trouve rien
    assert client.post("/models/rf_20260101_0000/deploy").status_code == 404
