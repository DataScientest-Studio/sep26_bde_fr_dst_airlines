import os,sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
def init_spark(appname:str="Airline"):
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    
    spark = (
        SparkSession.builder
        .appName(appname)
        .master("local[*]")
        .config(
            "spark.jars",
            "/opt/spark-extra-jars/gcs-connector.jar,/opt/spark-extra-jars/postgresql.jar"
        )
        .config(
            "spark.hadoop.fs.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem"
        )
        .config(
            "spark.hadoop.fs.AbstractFileSystem.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS"
        )
        .getOrCreate()
    )

    # Fix issue with gs config
    hconf = spark.sparkContext._jsc.hadoopConfiguration()

    hconf.set("fs.gs.block.size", "67108864")
    hconf.set("fs.gs.outputstream.buffer.size", "8388608")
    hconf.set("fs.gs.inputstream.inplace.seek.limit", "8388608")
    hconf.set("fs.gs.inputstream.min.range.request.size", "2097152")

    return spark