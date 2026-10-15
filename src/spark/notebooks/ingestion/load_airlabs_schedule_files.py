#!/usr/bin/env python
# coding: utf-8
from pathlib import Path
import os, sys
import tempfile

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config, init_spark
from pyspark.sql import functions as F
from google.cloud import storage
import common
import json
import debugpy
is_local=False
if os.getenv("RUN_ENV") == "docker":
    print("Docker execution")
else:
    print("Local debug")
    is_local=True
    
import pyspark
import os

print("PySpark :", pyspark.__version__)
print("SPARK_HOME :", os.environ.get("SPARK_HOME"))
print("JAVA_HOME :", os.environ.get("JAVA_HOME"))

# Read all CSV from Bucket

def read_input(bucket_name, prefix, gcp_project, use_temp_file:bool=False):
    df=None
    print(f"Read files from {bucket_name}/{prefix}")
    client = storage.Client(project=gcp_project)
    bucket = client.bucket(bucket_name)
    files=[]
    tempfiles=[]
    blobs = list(
        client.list_blobs(
            bucket_name,
            prefix=prefix
        )
    )
    local_file=''
    for blob in blobs:
        try:
            if blob.name.endswith(".csv"):
                print(f"  + Load : 'gs://{bucket_name}/{blob.name}'")

                if use_temp_file:
                    with tempfile.NamedTemporaryFile(
                        suffix=".csv",
                        delete=False
                    ) as tmp:
                        local_file = tmp.name

                    blob.download_to_filename(local_file) 
                    
                    dff = (
                        spark.read
                        .option("header", True)
                        .option("inferSchema", False)
                        .csv(local_file)
                        .withColumn(
                            "source_file",
                            F.lit(os.path.basename(blob.name))
                        )
                    )
                    
                else:
                    dff = (spark.read
                        .option("header", True)
                        .option("inferSchema", False)
                        .csv(f"gs://{bucket_name}/{blob.name}")
                        .withColumn("source_file", F.lit(os.path.basename(blob.name)))
                        )
                
                if df is None:
                    df=dff
                else:
                    df = df.unionByName(dff)
                if dff is not None:
                    print(f"     {dff.count()} row(s) loaded")
                    files.append(blob.name)
        except Exception as e:
            print(f"     Error {e}")
            import traceback
            traceback.print_exc()
        finally:
            if os.path.isfile(local_file): os.remove(local_file)
    if df is None:        
        return None,[]
    print(f"{df.count()} row(s) read from bucket")
    # Drop empty lines
    df = df.na.drop(how="all")
    # Keep only landed
    df = df.filter(df["status"]=="landed")
    # Keep only rows with mandatory column filled
    df = df.filter(
        F.col("airline_icao").isNotNull() &
        F.col("flight_number").isNotNull() &
        F.col("dep_iata").isNotNull() &
        F.col("dep_time").isNotNull() &
        F.col("arr_iata").isNotNull()
    )
    # Convert Types ...
    df = df.withColumn("dep_time", F.to_timestamp("dep_time")) \
        .withColumn("arr_time", F.to_timestamp("arr_time")) \
        .withColumn("arr_estimated", F.to_timestamp("arr_estimated")) \
        .withColumn("arr_actual", F.to_timestamp("arr_actual")) \
        .withColumn("dep_estimated", F.to_timestamp("dep_estimated")) \
        .withColumn("dep_actual", F.to_timestamp("dep_actual")) \
        .withColumn("duration", F.col("duration").cast("integer")) \
        .withColumn("dep_delayed", F.col("dep_delayed").cast("integer")) \
        .withColumn("arr_delayed", F.col("arr_delayed").cast("integer"))
    # Drop duplicates
    df = df.dropDuplicates([
        "airline_icao",
        "flight_number",
        "dep_iata",
        "dep_time",
        "arr_iata"
    ])
    print(f"{df.count()} row(s) after cleaning for {len(files)} file(s)")
    return df, files


# Insert in Temp table
def load_temp(df, host,db, user, password,port=5432):
    from sqlalchemy import create_engine, text
    import uuid

    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    with engine.begin() as conn:
        # Create Schema if necessary
        try:
            sql=f"""CREATE SCHEMA IF NOT EXISTS temp;"""
            conn.execute(text(sql))
        except:
            pass      
    # Staging table (eq to Temp)
    staging_table = f"temp.staging_airlabs_schedule_{str(uuid.uuid4()).replace('-', '')}"
    jdbc_url = (
        f"jdbc:postgresql://{host}:{port}/{db}"
    )

    properties = {
        "user": user,
        "password": password,
        "driver": "org.postgresql.Driver"
    }

    df.write.jdbc(
                url=jdbc_url,
                table=staging_table,
                mode="overwrite",
                properties=properties
            )
    if df is not None:
        print(f"{df.count()} row loaded in temp")
    else:
        print(f"No row loaded in temp")
    return staging_table


# In[15]:


# Insert in target table
from sqlalchemy import create_engine, text

def insert(staging_table,host, db,user,password, port=5432, table="raw.airlabs_schedules" ):
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    with engine.begin() as conn:
        try:
            # Create Schema if necessary
            try:
                sql=f"""CREATE SCHEMA IF NOT EXISTS raw;"""
                conn.execute(text(sql))
            except:
                pass      

            # Insert query
            sql = f"""
            INSERT INTO {table} (
                airline_icao,
                flight_icao,
                flight_number,
                dep_iata,
                dep_time,
                arr_iata,
                arr_time,
                arr_estimated,
                arr_actual,
                cs_flight_iata,
                status,
                duration,
                dep_delayed,
                arr_delayed,
                dep_estimated,
                dep_actual,
                source_file
            )
            SELECT DISTINCT
                s.airline_icao,
                s.flight_icao,
                s.flight_number,
                s.dep_iata,
                s.dep_time,
                s.arr_iata,
                s.arr_time,
                s.arr_estimated,
                s.arr_actual,
                s.cs_flight_iata,
                s.status,
                s.duration,
                s.dep_delayed,
                s.arr_delayed,
                s.dep_estimated,
                s.dep_actual,
                s.source_file
            FROM {staging_table} s
            ON CONFLICT (
                airline_icao,
                flight_number,
                dep_iata,
                dep_time,
                arr_iata
            )
            DO NOTHING;"""

            inserted= conn.execute(text(sql))
            print(f"{inserted} new data found")
        except Exception as e:
            raise Exception(f"Error Inserting data : {e}")
        finally:
            conn.execute(text(
                f"DROP TABLE IF EXISTS {staging_table}"
        ))


# In[8]:



def move(bucket_name,source_prefix, loaded_prefix, files, gcp_project):
    """ Move input files to backup folder
        @param bucket_name : Name of GCP Bucket
        @param source_prefix : Path to input folder
        @param loaded_prefix : Path to Backup
        @param files : List of files to move
        @param gcp_project : Project owning Bucket
    """
    client = storage.Client(project=gcp_project)
    bucket = client.bucket(bucket_name)

    blobs = list(
        client.list_blobs(
            bucket_name,
            prefix=source_prefix
        )
    )
    n=0
    for blob in blobs:
        # Skip folders
        if blob.name.endswith("/"):
            continue
        if blob.name in files:    
            destination = blob.name.replace(
                source_prefix,
                loaded_prefix,
                1
            )

            bucket.copy_blob(
                blob,
                bucket,
                destination
            )

            blob.delete()

            print(f"{blob.name} -> {destination}")

            n+=1
    print(f"{n} file(s) processed")


# Entry point
spark = init_spark()
if __name__== "__main__":
    try:
        try:
            config = Config(__file__)
            config.get_secrets()
            BUCKET = config["BUCKET"] #"liora-airline-project"
            PREFIX = config["PREFIX"] #"raw/airlabs"
            PREFIX_LOADED = config["PREFIX_LOADED"] #"raw/processed/airlabs"
            PROJECT = config.GCP_PROJECT
            if is_local:
                PG_HOST="localhost"
            else:
                PG_HOST = config.PG_HOST # "database"
            PG_PORT = config.PG_PORT # "5432"
            PG_DB = config.PG_DB #"airline"
            PG_USER = config.PG_USER #"batch"
                
            TARGET_TABLE = config.TARGET_TABLES["AIRLABS_SCHEDULES"] #"raw.airlabs_schedules"
            
            bucket_creds= config.AIRLINEBUCKET_CREDENTIALS
            password = config.AIRLINEDB_PASSWORD
        except Exception as e:
            raise Exception(f"Config error : {e}")

        # Read files from Bucket
        df, files = read_input(BUCKET, PREFIX, PROJECT)
        # Load temp file
        if df is not None:
            staging_table = load_temp(df, PG_HOST,PG_DB, PG_USER, password, PG_PORT)
            # Insert new informations
            insert(staging_table,PG_HOST,PG_DB, PG_USER, password, PG_PORT, table=TARGET_TABLE )
        
        # Move processed files
        move(BUCKET,PREFIX, PREFIX_LOADED, files, PROJECT)

        print("Load finished")
        sys.exit(0)
    except Exception as e:
        print (f"Error : {e}")
        sys.exit(1)

