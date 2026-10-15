import argparse
from pyspark.sql import SparkSession
import os
import requests



URL_OPDI = "https://www.eurocontrol.int/performance/data/download/OPDI/v002/flight_list/flight_list_{mois}.parquet"


def telecharger(months, dossier):
    """Télécharge chaque mois dans `dossier` et renvoie la liste des fichiers."""
    os.makedirs(dossier, exist_ok=True)
    fichiers = []
    for mois in months:
        chemin = os.path.join(dossier, f"flight_list_{mois}.parquet")
        r = requests.get(URL_OPDI.format(mois=mois), timeout=300)
        r.raise_for_status()
        with open(chemin, "wb") as f:
            f.write(r.content)
        print(f"{mois} : {len(r.content) / 1e6:.0f} Mo")
        fichiers.append(chemin)
    return fichiers

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True, help="Mois AAAAMM, ex. 202508 202509")
    args = parser.parse_args()

    spark = (
    SparkSession.builder
    .appName("collect_opdi")
    .config("spark.jars", "/opt/spark-extra-jars/gcs-connector.jar")
    .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    .getOrCreate()
)


    fichiers = telecharger(args.months, "/tmp/opdi")

    df = spark.read.option("mergeSchema", "true").parquet(*fichiers)
    print(f"{df.count()} lignes lues")

    df.write.mode("overwrite").parquet("gs://liora-airline-project/raw/opdi/")
    print("Écrit dans gs://liora-airline-project/raw/opdi/")



if __name__ == "__main__":
    main()