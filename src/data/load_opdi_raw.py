import argparse
import getpass
import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PARIS = ["LFPG", "LFPO", "LFOB"]
COLONNES_DATES = ["dof", "first_seen", "last_seen"]


def get_spark():
    spark = (
        SparkSession.builder
        .appName("load_opdi_raw")
        .config("spark.jars", "/opt/spark-extra-jars/gcs-connector.jar,/opt/spark-extra-jars/postgresql.jar")
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
        .config("spark.sql.session.timeZone", "UTC") #date UTC dans les données
        .getOrCreate()
    )
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.gs.block.size", "67108864")
    hconf.set("fs.gs.outputstream.buffer.size", "8388608")
    hconf.set("fs.gs.inputstream.inplace.seek.limit", "8388608")
    hconf.set("fs.gs.inputstream.min.range.request.size", "2097152")
    return spark


def lire_mois(spark, mois):
    """Lit un mois, harmonise les dates, garde les vols Paris."""
    df = spark.read.parquet(f"gs://liora-airline-project/raw/opdi/mois={mois}/")
    for col in COLONNES_DATES:
        df = df.withColumn(col, F.to_timestamp(col))
    df = df.filter(F.col("adep").isin(PARIS) | F.col("ades").isin(PARIS))
    return df.withColumn("mois", F.lit(mois))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True)
    args = parser.parse_args()

    spark = get_spark()

    df = None
    for mois in args.months:
        d = lire_mois(spark, mois)
        df = d if df is None else df.unionByName(d, allowMissingColumns=True)

    pwd = os.environ.get("PG_PASSWORD") or getpass.getpass("Mot de passe PG : ")
    (df.write.format("jdbc")
       .option("url", "jdbc:postgresql://database:5432/airline")
       .option("dbtable", "raw.opdi_flights")
       .option("user", "pascal")
       .option("password", pwd)
       .option("driver", "org.postgresql.Driver")
       .mode("overwrite")
       .save())
    print(f"{df.count()} lignes chargées dans raw.opdi_flights")


if __name__ == "__main__":
    main()