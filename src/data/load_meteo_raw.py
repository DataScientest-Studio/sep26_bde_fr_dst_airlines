import getpass
import os

import psycopg2
from psycopg2 import sql
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PATH_METEO = "gs://liora-airline-project/raw/meteo/"
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
        .appName("load_meteo_raw")
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


def read_meteo_dir(spark):
    """Read the weather parquet files and convert time to timestamp."""
    df = spark.read.parquet(PATH_METEO)
    return df.withColumn("time", F.to_timestamp("time"))


def main():
    spark = get_spark()
    df = read_meteo_dir(spark)
    df.printSchema()

    pwd = os.environ.get("PG_PASSWORD") or getpass.getpass("PG password: ")
    (df.repartition(4)
       .write.format("jdbc")
       .option("url", f"jdbc:postgresql://{PG_HOST}:5432/{PG_DB}")
       .option("dbtable", "raw.meteo_hourly")
       .option("user", PG_USER)
       .option("password", pwd)
       .option("driver", "org.postgresql.Driver")
       .option("batchsize", 10000)
       .mode("overwrite")
       .save())

    for role in ROLES:
        all_grants(pwd, "raw.meteo_hourly", role)
    print(f"{df.count()} rows written to raw.meteo_hourly")


if __name__ == "__main__":
    main()