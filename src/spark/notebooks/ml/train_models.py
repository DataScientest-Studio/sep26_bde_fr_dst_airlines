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
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

is_local = os.getenv("RUN_ENV") != "docker"

CONFIG_FILE = str(Path(__file__).resolve().parent.parent / "ingestion" / "config.json")
FEATURES_TABLE = "gold.ml_flights_features"

TARGET = "delay"
CATEGORICAL_FEATURES = ["airline_icao", "adep", "ades"]
NUMERIC_FEATURES = [
    "dow",
    "arr_hour_local",
    "arr_temperature_2m",
    "arr_temp_dew_spread",
    "arr_relative_humidity_2m",
    "arr_pressure_msl",
    "arr_cloud_cover",
    "arr_cloud_cover_low",
    "arr_cloud_cover_mid",
    "arr_cloud_cover_high",
    "arr_wind_speed_10m",
    "arr_wind_direction_sin",
    "arr_wind_direction_cos",
    "arr_wind_gusts_10m",
    "arr_precipitation",
    "arr_snowfall",
    "arr_weather_code",
]
TEST_SIZE = 0.2
RANDOM_STATE = 42


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


# Prepare data for training
def prepare_data(df):
    """ Drop flights without weather, split train/test by random whole days
        (Paris local date of the scheduled arrival) and build the preprocessing step
        shared by all models.
        @return X_train, X_test, y_train, y_test, preprocessor
    """
    nb_before = len(df)
    df = df.dropna(subset=["arr_temperature_2m"]).copy()
    print(f"{nb_before - len(df)} flight(s) without weather dropped, {len(df)} kept")

    df["dow"] = df["dow"].astype(int)
    df["arr_hour_local"] = df["arr_hour_local"].astype(int)
    days = df["sched_arr_utc"].dt.tz_convert("Europe/Paris").dt.date

    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df[TARGET].astype(int)

    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(X, y, groups=days))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    test_days = sorted(days.iloc[test_idx].unique())
    print(f"Train : {len(X_train)} row(s), {days.iloc[train_idx].nunique()} day(s), {y_train.mean():.1%} delayed")
    print(f"Test  : {len(X_test)} row(s), {len(test_days)} day(s), {y_test.mean():.1%} delayed")
    print(f"Test days : {', '.join(str(d) for d in test_days)}")

    preprocessor = ColumnTransformer([
        ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ("numeric", "passthrough", NUMERIC_FEATURES),
    ])
    return X_train, X_test, y_train, y_test, preprocessor


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

        # Prepare data
        X_train, X_test, y_train, y_test, preprocessor = prepare_data(df)

        print("Training finished")
        sys.exit(0)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)