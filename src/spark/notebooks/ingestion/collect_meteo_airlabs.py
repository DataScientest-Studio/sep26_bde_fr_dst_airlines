#!/usr/bin/env python
# coding: utf-8
"""
Collect hourly weather (Open-Meteo archive) for the airports of AirLabs flights
and append it to raw.meteo_hourly.

Steps:
  1. Read config and secrets (same pattern as load_airlabs_schedule_files.py)
  2. Read raw tables: days with flights per airport (raw.airlabs_schedules,
     dep_icao / arr_icao), compared with the days already complete (24 hours)
     in raw.meteo_hourly
  3. Build the list of calls (one per airport, covering its missing days)
  4. Call the Open-Meteo archive API
  5. Load the result in a staging table, then INSERT ... ON CONFLICT DO NOTHING

"""
from pathlib import Path
import os, sys
import time
from datetime import datetime, timedelta, timezone

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config, init_spark
import pandas as pd
import requests
from sqlalchemy import create_engine, text

is_local = False
if os.getenv("RUN_ENV") == "docker":
    print("Docker execution")
else:
    print("Local debug")
    is_local = True

API_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARIABLES = [
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
    "rain",
    "snowfall",
    "weather_code",
]


# Read raw tables and build the list of calls
def list_calls(host, db, user, password, port, end_date, table):
    """ Compare the days with flights (raw.airlabs_schedules) with the days already
        complete in the weather table (24 hours), and return one call per airport
        covering its missing days.
        @param end_date : last day available in the archive
        @param table : weather raw table
    """
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    sql = f"""
    with flights as (
        select dep_icao as icao, cast(dep_time as date) as day
        from raw.airlabs_schedules where dep_icao is not null
        union
        select arr_icao, cast(arr_time as date)
        from raw.airlabs_schedules where arr_icao is not null
    ),
    present as (
        select icao, cast(time as date) as day
        from {table}
        group by 1, 2
        having count(*) = 24
    ),
    missing as (
        select f.icao, f.day
        from flights f
        left join present p on p.icao = f.icao and p.day = f.day
        where p.icao is null
          and f.day <= :end_date
    ),
    coords as (
        select distinct on (icao_code)
            icao_code,
            cast(lat as float) as latitude,
            cast(lng as float) as longitude
        from raw.airlabs_airports
        where icao_code <> '' and lat <> '' and lng <> ''
        order by icao_code, length(lat) desc, lat, lng
    )
    select m.icao, c.latitude, c.longitude,
           min(m.day) as start_date,
           max(m.day) as end_date,
           count(*) as nb_days
    from missing m
    join coords c on c.icao_code = m.icao
    group by 1, 2, 3
    order by 1
    """
    with engine.connect() as conn:
        missing = pd.read_sql(text(sql), conn, params={"end_date": end_date})

    calls = missing.to_dict("records")
    nb_days = int(missing["nb_days"].sum()) if calls else 0
    print(f"{len(calls)} airport(s) to collect, {nb_days} missing day(s)")
    return calls


# Call Open-Meteo archive
def fetch_weather(calls, wait_s=1):
    """ Call the API for each airport. Stops at the first HTTP 429 (quota):
        data already collected is kept, the next run resumes the rest.
    """
    frames = []
    done = 0
    for call in calls:
        start = pd.Timestamp(call["start_date"]).strftime("%Y-%m-%d")
        end = pd.Timestamp(call["end_date"]).strftime("%Y-%m-%d")
        params = {
            "latitude": call["latitude"],
            "longitude": call["longitude"],
            "start_date": start,
            "end_date": end,
            "hourly": ",".join(HOURLY_VARIABLES),
            "timezone": "UTC",
        }
        try:
            response = requests.get(API_URL, params=params, timeout=60)
            if response.status_code == 429:
                print(f"  ! Quota reached after {done} call(s), stop here")
                break
            response.raise_for_status()
            hourly = response.json()["hourly"]
            dff = pd.DataFrame(hourly)
            dff["icao"] = call["icao"]
            dff["time"] = pd.to_datetime(dff["time"], utc=True)
            frames.append(dff)
            done += 1
            print(f"  + {call['icao']} {start} -> {end} : {len(dff)} row(s)")
        except Exception as e:
            print(f"  ! {call['icao']} error : {e}")
        time.sleep(wait_s)
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    print(f"{len(df)} row(s) collected for {done} airport(s)")
    return df


# Insert in Temp table
def load_temp(spark, pdf, host, db, user, password, port=5432):
    import uuid
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS temp;"))
    staging_table = f"temp.staging_meteo_hourly_{str(uuid.uuid4()).replace('-', '')}"
    jdbc_url = f"jdbc:postgresql://{host}:{port}/{db}"
    properties = {
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver"
    }
    df = spark.createDataFrame(pdf[["icao", "time"] + HOURLY_VARIABLES])
    df.write.jdbc(
        url=jdbc_url,
        table=staging_table,
        mode="overwrite",
        properties=properties
    )
    print(f"{df.count()} row(s) loaded in temp")
    return staging_table


# Insert in target table (existing hours are skipped)
def insert(staging_table, host, db, user, password, port=5432, table="raw.meteo_hourly"):
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    columns = ", ".join(["icao", "time"] + HOURLY_VARIABLES)
    with engine.begin() as conn:
        try:
            sql = f"""
            INSERT INTO {table} ({columns})
            SELECT {columns}
            FROM {staging_table}
            ON CONFLICT (icao, time) DO NOTHING;"""
            inserted = conn.execute(text(sql))
            print(f"{inserted.rowcount} new row(s) inserted in {table}")
        except Exception as e:
            raise Exception(f"Error Inserting data : {e}")
        finally:
            conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))


# Entry point
spark = init_spark("collect_meteo_airlabs")
spark.conf.set("spark.sql.session.timeZone", "UTC")
if __name__ == "__main__":
    try:
        try:
            config = Config(__file__)
            config.get_secrets()
            if is_local:
                PG_HOST = "localhost"
            else:
                PG_HOST = config.PG_HOST
            PG_PORT = config.PG_PORT
            PG_DB = config.PG_DB
            PG_USER = config.PG_USER
            password = config.AIRLINEDB_PASSWORD

            TARGET_TABLE = config.TARGET_TABLES.get("METEO_HOURLY", "raw.meteo_hourly")
            ARCHIVE_DELAY_DAYS = int(config.config_content.get("METEO_ARCHIVE_DELAY_DAYS", 5))
        except Exception as e:
            raise Exception(f"Config error : {e}")

        END_DATE = datetime.now(timezone.utc).date() - timedelta(days=ARCHIVE_DELAY_DAYS)
        print(f"Last day available in the archive : {END_DATE}")

        # Read raw tables and list the calls
        calls = list_calls(PG_HOST, PG_DB, PG_USER, password, PG_PORT, END_DATE, TARGET_TABLE)

        # Call the API
        pdf = fetch_weather(calls) if calls else None

        # Load temp table and insert new hours
        if pdf is not None:
            staging_table = load_temp(spark, pdf, PG_HOST, PG_DB, PG_USER, password, PG_PORT)
            insert(staging_table, PG_HOST, PG_DB, PG_USER, password, PG_PORT, table=TARGET_TABLE)

        print("Collect finished")
        sys.exit(0)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)