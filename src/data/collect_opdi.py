import argparse
import os

import requests
from pyspark.sql import SparkSession

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
    hconf = spark.sparkContext._jsc.hadoopConfiguration()
    hconf.set("fs.gs.block.size", "67108864")
    hconf.set("fs.gs.outputstream.buffer.size", "8388608")
    hconf.set("fs.gs.inputstream.inplace.seek.limit", "8388608")
    hconf.set("fs.gs.inputstream.min.range.request.size", "2097152")

    fichiers = telecharger(args.months, "/tmp/opdi")

    for mois, fichier in zip(args.months, fichiers):
        df = spark.read.parquet(fichier)
        destination = f"gs://liora-airline-project/raw/opdi/mois={mois}/"
        df.write.mode("overwrite").parquet(destination)
        print(f"{mois} : {df.count()} lignes écrites dans {destination}")


if __name__ == "__main__":
    main()