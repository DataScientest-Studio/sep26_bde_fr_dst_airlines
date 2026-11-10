import numpy as np
import pytest

from api.ml_model import ml_manager

FLIGHT = {
    "flight": {
        "airline_icao": "AFR", "dep_icao": "LFPG", "arr_icao": "LFMN",
        "flight_date": "2026-11-10", "arr_time": "10:30",
        "arr_lat": "43.65", "arr_lng": "7.21",
    }
}
WEATHER = {
    "temperature_2m": 10, "dew_point_2m": 5, "relative_humidity_2m": 70, "pressure_msl": 1010,
    "cloud_cover": 50, "cloud_cover_low": 10, "cloud_cover_mid": 20, "cloud_cover_high": 30,
    "wind_speed_10m": 12, "wind_direction_10m": 90, "wind_gusts_10m": 20,
    "precipitation": 0, "snowfall": 0, "weather_code": 1,
}


class DummyModel:
    def predict(self, df):
        return [20.0] * len(df)

    def predict_proba(self, df):
        return np.array([[0.3, 0.7]] * len(df))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr("api.ml_model.get_weather", lambda *a, **k: WEATHER)


def test_predict_without_model_is_503(client, monkeypatch):
    monkeypatch.setattr(ml_manager, "model", None)
    assert client.post("/predict", json=FLIGHT).status_code == 503


def test_predict_single(client, monkeypatch):
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict", json=FLIGHT)
    assert r.status_code == 200
    body = r.json()
    assert body["is_delayed"] is True
    assert body["delay_probability"] == pytest.approx(0.7)


def test_predict_batch(client, monkeypatch):
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict-batch", json={"flights": [FLIGHT, FLIGHT]})
    assert r.status_code == 200
    assert len(r.json()["predictions"]) == 2


def test_predict_empty_batch(client, monkeypatch):
    monkeypatch.setattr(ml_manager, "model", DummyModel())
    r = client.post("/predict-batch", json={"flights": []})
    assert r.json() == {"predictions": []}


def test_build_features_columns():
    from api.flight_predictor import build_features

    row = build_features({**FLIGHT["flight"]}, WEATHER)
    assert row["adep"] == "LFPG" and row["ades"] == "LFMN"
    assert row["arr_hour_local"] == 10
    assert row["dow"] == 2  # mardi
    assert row["arr_temp_dew_spread"] == 5


@pytest.mark.parametrize("name", ["a b", "x;drop", "..%2Fetc"])
def test_deploy_rejects_bad_names(client, name):
    assert client.post(f"/models/{name}/deploy").status_code in (404, 422)


def test_deploy_unknown_model_is_404(client, fake_db):
    fake_db.rows = []
    assert client.post("/models/rf_20260101_0000/deploy").status_code == 404
