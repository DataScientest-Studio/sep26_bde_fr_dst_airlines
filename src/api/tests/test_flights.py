import pytest

from api.schemas import FlightSearch

BASE = {
    "airline_name": "Air France",
    "origin_airport": "CDG",
    "destination_airport": "NCE",
    "flight_date": "2026-11-08",  # dimanche
}


def test_search_defaults_are_not_tuples():
    s = FlightSearch()
    assert s.limit == 100 and s.offset == 0 and s.flight_date is None


@pytest.mark.parametrize("missing", ["origin_airport", "destination_airport", "flight_date", "airline_name"])
def test_missing_required_param_returns_422(client, missing):
    body = {k: v for k, v in BASE.items() if k != missing}
    assert client.post("/flights", json=body).status_code == 422


def test_bad_date_format_returns_422(client):
    r = client.post("/flights", json={**BASE, "flight_date": "08/11/2026"})
    assert r.status_code == 422


def test_limit_is_bounded(client):
    assert client.post("/flights", json={**BASE, "limit": 0}).status_code == 422
    assert client.post("/flights", json={**BASE, "limit": 100000}).status_code == 422


def test_airline_name_pattern_has_no_quotes(client, fake_db):
    assert client.post("/flights", json=BASE).status_code == 200
    _, params = fake_db.calls[0]
    assert params["airline_name"] == "%Air France%"


def test_dow_sunday_is_zero_and_monday_is_one(client, fake_db):
    client.post("/flights", json=BASE)  # 2026-11-08 = dimanche
    client.post("/flights", json={**BASE, "flight_date": "2026-11-09"})  # lundi
    assert fake_db.calls[0][1]["dow"] == 0
    assert fake_db.calls[1][1]["dow"] == 1


def test_optional_hours_can_be_omitted(client, fake_db):
    assert client.post("/flights", json=BASE).status_code == 200
    params = fake_db.calls[0][1]
    assert params["start_hour"] is None and params["end_hour"] is None


def test_hours_are_formatted(client, fake_db):
    client.post("/flights", json={**BASE, "start_hour": 6, "end_hour": 12})
    params = fake_db.calls[0][1]
    assert (params["start_hour"], params["end_hour"]) == ("06:00", "12:00")


def test_airline_codes_alone_is_enough(client, fake_db):
    body = {k: v for k, v in BASE.items() if k != "airline_name"}
    r = client.post("/flights", json={**body, "airline_codes": ["AFR", "EZY"]})
    assert r.status_code == 200
    assert "airline_codes" in fake_db.calls[0][0]


def test_db_error_returns_500_without_leaking_details(client, fake_db):
    fake_db.error = RuntimeError("password=secret host=internal")
    r = client.post("/flights", json=BASE)
    assert r.status_code == 500
    assert "secret" not in r.text
