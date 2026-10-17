import argparse
import tempfile
import time
from datetime import datetime

import pandas as pd
import requests
from google.cloud import storage

# --- Parameters ---
URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2025-08-01"
END_DATE = "2026-07-31"
PAUSE_S = 30
WAIT_429_S = 60
MAX_429 = 3
BUCKET = "liora-airline-project"
PREFIX = "raw/meteo"

PARAMS = {
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": "temperature_2m,dew_point_2m,relative_humidity_2m,pressure_msl,"
              "cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,"
              "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
              "precipitation,rain,snowfall,weather_code",
    "timezone": "UTC",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--airports-file", required=True, help="CSV icao, latitude_deg, longitude_deg")
    args = parser.parse_args()

    bucket = storage.Client().bucket(BUCKET)

    airports = pd.read_csv(args.airports_file)
    no_coords = airports["latitude_deg"].isna() | airports["longitude_deg"].isna()
    print(f"Airports without coordinates (skipped): {no_coords.sum()}")
    airports = airports[~no_coords]

    failures_429 = 0
    for row in airports.itertuples(index=False):
        blob = bucket.blob(f"{PREFIX}/{row.icao}.parquet")
        if blob.exists():
            continue

        params = PARAMS.copy()
        params["latitude"] = row.latitude_deg
        params["longitude"] = row.longitude_deg
        try:
            r = requests.get(URL, params=params, timeout=60)
        except requests.RequestException as e:
            print(f"{datetime.now():%H:%M:%S} {row.icao} network error: {e}")
            continue

        if r.status_code == 200:
            try:
                df = pd.DataFrame(r.json()["hourly"])
            except (ValueError, KeyError):
                print(f"{datetime.now():%H:%M:%S} {row.icao} empty or invalid response")
                time.sleep(PAUSE_S)
                continue
            df["icao"] = row.icao
            with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
                df.to_parquet(tmp.name, index=False)
                blob.upload_from_filename(tmp.name)
            failures_429 = 0
            print(f"{datetime.now():%H:%M:%S} {row.icao} OK")
        elif r.status_code == 429:
            failures_429 += 1
            print(r.text)
            if failures_429 >= MAX_429:
                print(f"{MAX_429} refusals in a row: daily quota reached, run again tomorrow")
                break
            print(f"{datetime.now():%H:%M:%S} {row.icao} refused (429), waiting {WAIT_429_S} s")
            time.sleep(WAIT_429_S)
        else:
            print(f"{datetime.now():%H:%M:%S} {row.icao} error {r.status_code}")

        time.sleep(PAUSE_S)

    # --- Summary (based on the bucket) ---
    done = {b.name.split("/")[-1].removesuffix(".parquet") for b in bucket.list_blobs(prefix=PREFIX)}
    remaining = sorted(set(airports["icao"]) - done)
    print(f"Retrieved: {len(done)} / {len(airports)}")
    if remaining:
        print(f"Remaining ({len(remaining)}): {', '.join(remaining[:20])}{' ...' if len(remaining) > 20 else ''}")
    else:
        print("Collection complete")