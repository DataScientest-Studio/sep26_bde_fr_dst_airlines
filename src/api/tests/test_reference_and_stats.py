def test_airlines_returns_rows(client, fake_db):
    fake_db.rows = [{"iata_code": "AF", "airline_name": "Air France", "icao_code": "AFR"}]
    r = client.get("/airlines", params={"search": "air"})
    assert r.status_code == 200
    assert r.json()[0]["icao_code"] == "AFR"
    assert fake_db.calls[0][1]["pattern"] == "%air%"


def test_airports_filters_are_bound(client, fake_db):
    client.get("/airports", params={"country": "FR", "search": "ori"})
    params = fake_db.calls[0][1]
    assert params["country"] == "FR" and params["pattern"] == "%ori%"


def test_airports_db_error_is_a_clean_500(client, fake_db):
    fake_db.error = RuntimeError("boom")
    r = client.get("/airports")
    assert r.status_code == 500
    assert "boom" not in r.text


def test_airlines_db_error_is_a_clean_500(client, fake_db):
    fake_db.error = RuntimeError("boom")
    assert client.get("/airlines").status_code == 500


def test_stats_hour(client, fake_db):
    fake_db.rows = [{"arr_hour_local": 8, "nb_flights": 10, "nb_delayed": 2, "delay_rate": 0.2, "avg_delay_min": 25.0}]
    r = client.get("/stats/hour")
    assert r.status_code == 200
    assert r.json()[0]["delay_rate"] == 0.2
