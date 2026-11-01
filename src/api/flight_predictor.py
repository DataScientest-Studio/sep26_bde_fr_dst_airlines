from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from sqlalchemy import text

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_VARIABLES = [
    "temperature_2m",
    "dew_point_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "precipitation",
    "snowfall",
    "weather_code",
]


def get_weather(db, icao, flight_date, arr_time):
    """ Open-Meteo forecast at the arrival airport, for the arrival hour """
    arrival = datetime.strptime(f"{flight_date} {arr_time}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Paris"))
    arrival_utc = arrival.astimezone(timezone.utc)

    airport = db.execute(
        text("SELECT lat, lng FROM gold.dim_airports WHERE icao_code = :icao"),
        {"icao": icao},
    ).first()

    params = {
        "latitude": airport.lat,
        "longitude": airport.lng,
        "hourly": ",".join(WEATHER_VARIABLES),
        "start_date": arrival_utc.strftime("%Y-%m-%d"),
        "end_date": arrival_utc.strftime("%Y-%m-%d"),
        "timezone": "UTC",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    hourly = response.json()["hourly"]

    i = hourly["time"].index(arrival_utc.strftime("%Y-%m-%dT%H:00"))
    return {var: hourly[var][i] for var in WEATHER_VARIABLES}