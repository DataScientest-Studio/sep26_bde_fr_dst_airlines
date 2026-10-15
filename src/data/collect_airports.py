import getpass
import os
from datetime import datetime

import requests
from google.cloud import storage
from pyspark.sql import SparkSession

URL_AIRPORTS = "https://davidmegginson.github.io/ourairports-data/airports.csv"
BUCKET = "liora-airline-project"


def main():
    # 1. Téléchargement
    os.makedirs("/tmp/airports", exist_ok=True)
    chemin = "/tmp/airports/airports.csv"
    r = requests.get(URL_AIRPORTS, timeout=300)
    r.raise_for_status()
    with open(chemin, "wb") as f:
        f.write(r.content)
    print(f"airports.csv : {len(r.content) / 1e6:.1f} Mo")

    # 2. Archive du CSV brut dans le bucket, daté
    blob = f"raw/airports/airports_{datetime.now():%Y%m%d}.csv"
    storage.Client().bucket(BUCKET).blob(blob).upload_from_filename(chemin)
    print(f"Archivé : gs://{BUCKET}/{blob}")

    # 3. Chargement dans raw.airports
    spark = (
        SparkSession.builder
        .appName("collect_airports")
        .config("spark.jars", "/opt/spark-extra-jars/postgresql.jar")
        .getOrCreate()
    )
    df = spark.read.csv(chemin, header=True, inferSchema=True)

    pwd = os.environ.get("PG_PASSWORD") or getpass.getpass("Mot de passe PG : ")
    (df.write.format("jdbc")
       .option("url", "jdbc:postgresql://database:5432/airline")
       .option("dbtable", "raw.airports")
       .option("user", "pascal")
       .option("password", pwd)
       .option("driver", "org.postgresql.Driver")
       .mode("overwrite")
       .save())
    print(f"{df.count()} aéroports chargés dans raw.airports")


if __name__ == "__main__":
    main()