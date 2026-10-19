import argparse
import getpass
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

import psycopg2
from psycopg2 import sql



PARIS = ["LFPG", "LFPO", "LFOB"]
COLUMNS_DATE = ["dof", "first_seen", "last_seen"]
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


def get_spark():
    spark = (
        SparkSession.builder
        .appName("load_opdi_raw")
        .config("spark.jars", "/opt/spark-extra-jars/gcs-connector.jar,/opt/spark-extra-jars/postgresql.jar")
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
        .config("spark.sql.session.timeZone", "UTC") #date UTC used
        .getOrCreate()
    )
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.gs.block.size", "67108864")
    hconf.set("fs.gs.outputstream.buffer.size", "8388608")
    hconf.set("fs.gs.inputstream.inplace.seek.limit", "8388608")
    hconf.set("fs.gs.inputstream.min.range.request.size", "2097152")
    return spark


def read_opdi_dir(spark, month):
    """Read an OPDI month directory, convert dates to timestamps, keep Paris flights."""
    df = spark.read.parquet(f"gs://liora-airline-project/raw/opdi/mois={month}/")
    for col in COLUMNS_DATE:
        df = df.withColumn(col, F.to_timestamp(col))
    df = df.filter(F.col("adep").isin(PARIS) | F.col("ades").isin(PARIS))
    return df.withColumn("month", F.lit(month))



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True)
    args = parser.parse_args()

    spark = get_spark()

    df = None
    for month in args.months:
        d = read_opdi_dir(spark, month)
        df = d if df is None else df.unionByName(d, allowMissingColumns=True)

    pwd = os.environ.get("PG_PASSWORD") or getpass.getpass("PG password: ")
    (df.write.format("jdbc")
       .option("url", f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}")
       .option("dbtable", "raw.opdi_flights")
       .option("user", PG_USER)
       .option("password", pwd)
       .option("driver", "org.postgresql.Driver")
       .mode("overwrite")
       .save())

    for role in ROLES:
        all_grants(pwd, "raw.opdi_flights", role)
    print(f"{df.count()} rows written to raw.opdi_flights")


if __name__ == "__main__":
    main()