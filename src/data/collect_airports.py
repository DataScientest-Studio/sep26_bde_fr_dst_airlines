import getpass
import os
from datetime import datetime

import psycopg2
import requests
from google.cloud import storage
from psycopg2 import sql
from pyspark.sql import SparkSession

URL_AIRPORTS = "https://davidmegginson.github.io/ourairports-data/airports.csv"
BUCKET = "liora-airline-project"
ROLES = ["herve", "batch", "airflow"]

PG_HOST = os.environ.get("PG_HOST", "database")
PG_DB = os.environ.get("PG_DB", "airline")
PG_USER = os.environ.get("PG_USER", "pascal")


def all_grants(pwd, table, role):
    """Grant all privileges on a table to the given role or group."""
    schema, name = table.split(".")
    conn = psycopg2.connect(host=PG_HOST, dbname=PG_DB, user=PG_USER, password=pwd)
    with conn, conn.cursor() as cur:
        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON {}.{} TO {}").format(
                sql.Identifier(schema), sql.Identifier(name), sql.Identifier(role)
            )
        )
    conn.close()
    print(f"Privileges on {table} granted to: {role}")


def main():
    # Download
    os.makedirs("/tmp/airports", exist_ok=True)
    path = "/tmp/airports/airports.csv"
    r = requests.get(URL_AIRPORTS, timeout=300)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"airports.csv: {len(r.content) / 1e6:.1f} MB")

    # Archive the raw CSV in the bucket, dated
    blob = f"raw/airports/airports_{datetime.now():%Y%m%d}.csv"
    storage.Client().bucket(BUCKET).blob(blob).upload_from_filename(path)
    print(f"Archived: gs://{BUCKET}/{blob}")

    # Load into raw.airports
    spark = (
        SparkSession.builder
        .appName("collect_airports")
        .config("spark.jars", "/opt/spark-extra-jars/postgresql.jar")
        .getOrCreate()
    )
    df = spark.read.csv(path, header=True, inferSchema=True)

    pwd = os.environ.get("PG_PASSWORD") or getpass.getpass("PG password: ")
    (df.write.format("jdbc")
       .option("url", f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}")
       .option("dbtable", "raw.airports")
       .option("user", PG_USER)
       .option("password", pwd)
       .option("driver", "org.postgresql.Driver")
       .mode("overwrite")
       .save())
    

    for role in ROLES:
        all_grants(pwd, "raw.airports", role)
    print(f"{df.count()} rows written to raw.airports")


if __name__ == "__main__":
    main()