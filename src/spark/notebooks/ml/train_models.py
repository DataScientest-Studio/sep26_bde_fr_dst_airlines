#!/usr/bin/env python
# coding: utf-8
"""
Train delay prediction models (scikit-learn) and store their scores.
"""
from pathlib import Path
import os, sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config
import pandas as pd
from sqlalchemy import create_engine, text

is_local = os.getenv("RUN_ENV") != "docker"

CONFIG_FILE = str(Path(__file__).resolve().parent.parent / "ingestion" / "config.json")
FEATURES_TABLE = "gold.ml_flights_features"


# Read the training table
def read_features(host, db, user, password, port, table):
    """ Read the training table into a pandas DataFrame
        @param table : schema.table to read
    """
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    )
    with engine.connect() as conn:
        df = pd.read_sql(text(f"select * from {table}"), conn)
    print(f"{len(df)} row(s) read from {table}")
    return df


# Entry point
if __name__ == "__main__":
    try:
        try:
            config = Config(__file__, CONFIG_FILE)
            config.get_secrets()
            PG_HOST = "localhost" if is_local else config.PG_HOST
            PG_PORT = config.PG_PORT
            PG_DB = config.PG_DB
            PG_USER = config.PG_USER
            password = config.AIRLINEDB_PASSWORD
        except Exception as e:
            raise Exception(f"Config error : {e}")

        # Read the training table
        df = read_features(PG_HOST, PG_DB, PG_USER, password, PG_PORT, FEATURES_TABLE)
        print(df.dtypes)
        print(df["delay"].value_counts())

        print("Training finished")
        sys.exit(0)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)