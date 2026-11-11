import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

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


def get_weather(lat, lng, flight_date, arr_time):
    """ Open-Meteo forecast at the arrival airport, for the arrival hour """
    arrival = datetime.strptime(f"{str(flight_date)[:10]} {arr_time}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("Europe/Paris"))
    arrival_utc = arrival.astimezone(timezone.utc)

    params = {
        "latitude": lat,
        "longitude": lng,
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


def get_dep_weather(lat, lng, flight_date, dep_time):
    """ Open-Meteo forecast at the departure airport, for the departure hour.
        dep_time is the local time of the departure airport: with timezone=auto,
        Open-Meteo returns the hours in the local time of the airport, so no conversion is needed.
    """
    date = str(flight_date)[:10]
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": ",".join(WEATHER_VARIABLES),
        "start_date": date,
        "end_date": date,
        "timezone": "auto",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    hourly = response.json()["hourly"]

    i = hourly["time"].index(f"{date}T{dep_time[:2]}:00")
    return {var: hourly[var][i] for var in WEATHER_VARIABLES}


def build_features(flight, weather, dep_weather):
    """ One row with the columns of marts.mrt_ml_flights_features """
    arrival = datetime.strptime(f"{str(flight['flight_date'])[:10]} {flight['arr_time']}", "%Y-%m-%d %H:%M")
    direction = math.radians(weather["wind_direction_10m"])
    dep_direction = math.radians(dep_weather["wind_direction_10m"])
    return {
        "airline_icao": flight["airline_icao"],
        "adep": flight["dep_icao"],
        "ades": flight["arr_icao"],
        "dow": arrival.isoweekday(),
        "arr_hour_local": arrival.hour,
        "arr_temperature_2m": weather["temperature_2m"],
        "arr_temp_dew_spread": weather["temperature_2m"] - weather["dew_point_2m"],
        "arr_relative_humidity_2m": weather["relative_humidity_2m"],
        "arr_pressure_msl": weather["pressure_msl"],
        "arr_cloud_cover": weather["cloud_cover"],
        "arr_cloud_cover_low": weather["cloud_cover_low"],
        "arr_cloud_cover_mid": weather["cloud_cover_mid"],
        "arr_cloud_cover_high": weather["cloud_cover_high"],
        "arr_wind_speed_10m": weather["wind_speed_10m"],
        "arr_wind_direction_sin": math.sin(direction),
        "arr_wind_direction_cos": math.cos(direction),
        "arr_wind_gusts_10m": weather["wind_gusts_10m"],
        "arr_precipitation": weather["precipitation"],
        "arr_snowfall": weather["snowfall"],
        "arr_weather_code": weather["weather_code"],
        "dep_temperature_2m": dep_weather["temperature_2m"],
        "dep_temp_dew_spread": dep_weather["temperature_2m"] - dep_weather["dew_point_2m"],
        "dep_relative_humidity_2m": dep_weather["relative_humidity_2m"],
        "dep_pressure_msl": dep_weather["pressure_msl"],
        "dep_cloud_cover": dep_weather["cloud_cover"],
        "dep_cloud_cover_low": dep_weather["cloud_cover_low"],
        "dep_cloud_cover_mid": dep_weather["cloud_cover_mid"],
        "dep_cloud_cover_high": dep_weather["cloud_cover_high"],
        "dep_wind_speed_10m": dep_weather["wind_speed_10m"],
        "dep_wind_direction_sin": math.sin(dep_direction),
        "dep_wind_direction_cos": math.cos(dep_direction),
        "dep_wind_gusts_10m": dep_weather["wind_gusts_10m"],
        "dep_precipitation": dep_weather["precipitation"],
        "dep_snowfall": dep_weather["snowfall"],
        "dep_weather_code": dep_weather["weather_code"],
    }