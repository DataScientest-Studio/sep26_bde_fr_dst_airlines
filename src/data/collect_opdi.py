import argparse
import os

import requests
from pyspark.sql import SparkSession

URL_OPDI = "https://www.eurocontrol.int/performance/data/download/OPDI/v002/flight_list/flight_list_{month}.parquet"


def download(months, directory):
    """Download each month into `directory` and return the list of files."""
    os.makedirs(directory, exist_ok=True)
    files = []
    for month in months:
        path = os.path.join(directory, f"flight_list_{month}.parquet")
        r = requests.get(URL_OPDI.format(month=month), timeout=300)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"{month}: {len(r.content) / 1e6:.0f} MB")
        files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", nargs="+", required=True, help="Months YYYYMM, e.g. 202508 202509")
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

    files = download(args.months, "/tmp/opdi")

    for month, file in zip(args.months, files):
        df = spark.read.parquet(file)
        destination = f"gs://liora-airline-project/raw/opdi/mois={month}/"
        df.write.mode("overwrite").parquet(destination)
        print(f"{month}: {df.count()} rows written to {destination}")


if __name__ == "__main__":
    main()