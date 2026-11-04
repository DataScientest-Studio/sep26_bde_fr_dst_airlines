#!/usr/bin/env python
# coding: utf-8
"""
Fill the UTC columns of raw.airlabs_schedules for the rows already loaded (launched by hand, once).

"""
from pathlib import Path
import os, sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config, init_spark
from pyspark.sql import functions as F
from google.cloud import storage
from sqlalchemy import create_engine, text

is_local = os.getenv("RUN_ENV") != "docker"

OLD_PREFIX = "airlabs_raw/"


# Read the CSV of a folder of the bucket
def read_files(bucket_name, prefix, gcp_project, old_files):
    """ @return dataframe with the key of the flight and the 4 UTC columns """
    print(f"Read files from {bucket_name}/{prefix}")
    client = storage.Client(project=gcp_project)
    df = None
    nb_files = 0
    for blob in client.list_blobs(bucket_name, prefix=prefix):
        if not blob.name.endswith(".csv"):
            continue
        dff = (spark.read
            .option("header", True)
            .option("inferSchema", False)
            .csv(f"gs://{bucket_name}/{blob.name}")
            )
        if df is None:
            df = dff
        else:
            df = df.unionByName(dff, allowMissingColumns=True)
        nb_files += 1
    if df is None:
        print("  no file")
        return None
    print(f"  {nb_files} file(s) read")

    # Time used to find the row in raw
    if old_files:
        join_time = F.to_timestamp("dep_time_utc")
    else:
        join_time = F.to_timestamp("dep_time")

    df = df.filter(df["status"] == "landed").select(
        "airline_icao",
        "flight_number",
        "dep_iata",
        "arr_iata",
        join_time.alias("join_time"),
        F.to_timestamp("dep_time_utc").alias("dep_time_utc"),
        F.to_timestamp("arr_time_utc").alias("arr_time_utc"),
        F.to_timestamp("dep_actual_utc").alias("dep_actual_utc"),
        F.to_timestamp("arr_actual_utc").alias("arr_actual_utc"),
    )
    return df


# Insert in Temp table
def load_temp(df, host, db, user, password, port=5432):
    staging_table = "temp.staging_airlabs_utc"
    df.write.jdbc(
        url=f"jdbc:postgresql://{host}:{port}/{db}",
        table=staging_table,
        mode="overwrite",
        properties={"user": user, "password": password, "driver": "org.postgresql.Driver"},
    )
    print(f"{df.count()} row(s) loaded in {staging_table}")
    return staging_table


# Update the UTC columns of the target table
def update(staging_table, host, db, user, password, port=5432, table="raw.airlabs_schedules"):
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    with engine.begin() as conn:
        try:
            sql = f"""
            UPDATE {table} t
            SET dep_time_utc = s.dep_time_utc,
                arr_time_utc = s.arr_time_utc,
                dep_actual_utc = s.dep_actual_utc,
                arr_actual_utc = s.arr_actual_utc
            FROM {staging_table} s
            WHERE t.airline_icao = s.airline_icao
              AND t.flight_number = s.flight_number
              AND t.dep_iata = s.dep_iata
              AND t.arr_iata = s.arr_iata
              AND t.dep_time = s.join_time"""
            result = conn.execute(text(sql))
            print(f"{result.rowcount} row(s) updated in {table}")
        finally:
            conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))


# Entry point
spark = init_spark()
if __name__ == "__main__":
    try:
        try:
            config = Config(__file__)
            config.get_secrets()
            BUCKET = config["BUCKET"]
            PREFIX_LOADED = config["PREFIX_LOADED"]
            PROJECT = config.GCP_PROJECT
            PG_HOST = "localhost" if is_local else config.PG_HOST
            PG_PORT = config.PG_PORT
            PG_DB = config.PG_DB
            PG_USER = config.PG_USER
            TARGET_TABLE = config.TARGET_TABLES["AIRLABS_SCHEDULES"]
            password = config.AIRLINEDB_PASSWORD
        except Exception as e:
            raise Exception(f"Config error : {e}")

        old = read_files(BUCKET, OLD_PREFIX, PROJECT, old_files=True)
        new = read_files(BUCKET, PREFIX_LOADED, PROJECT, old_files=False)

        # Keep one row per flight
        df = old.unionByName(new).dropDuplicates([
            "airline_icao",
            "flight_number",
            "dep_iata",
            "join_time",
            "arr_iata"
        ])

        staging_table = load_temp(df, PG_HOST, PG_DB, PG_USER, password, PG_PORT)
        update(staging_table, PG_HOST, PG_DB, PG_USER, password, PG_PORT, table=TARGET_TABLE)

        print("Update finished")
    except Exception as e:
        print(f"Error : {e}")