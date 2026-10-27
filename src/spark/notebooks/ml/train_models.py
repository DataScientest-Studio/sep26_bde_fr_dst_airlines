#!/usr/bin/env python
# coding: utf-8
"""
Train delay prediction models (scikit-learn) and store their scores.

Steps:
  1. Read config and secrets (shared config.json of the ingestion folder)
  2. Read gold.ml_flights_features into a pandas DataFrame
  3. Prepare data: drop flights without weather, train/test split by random whole days
     (no day shared between train and test), preprocessing (one-hot for categories,
     numeric columns passed through)
  4. Train a RandomForest and an XGBoost, each in a Pipeline (preprocessing + model),
     named type_YYYYMMDD_HHMM
  5. Evaluate each model on the test set: confusion matrix (TP, FP, TN, FN),
     precision, recall, F1 (delay class) and ROC AUC
  6. Save each fitted pipeline with joblib in MODELS_DIR as <model_name>.joblib
  (next step to come: store results)
"""
from pathlib import Path
import os, sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config
import joblib
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

is_local = os.getenv("RUN_ENV") != "docker"

CONFIG_FILE = str(Path(__file__).resolve().parent.parent / "ingestion" / "config.json")
FEATURES_TABLE = "gold.ml_flights_features"
MODELS_DIR = Path("/app/workspace/models")

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


# Train the models
def train_models(X_train, y_train, preprocessor, run_stamp):
    """ Train one Pipeline (preprocessing + model) per model type.
        @param run_stamp : YYYYMMDD_HHMM, shared by all models of the same run
        @return dict {model_name: (model_type, fitted pipeline, training duration in s)}
    """
    nb_on_time = int((y_train == 0).sum())
    nb_delayed = int((y_train == 1).sum())
    pos_weight = nb_on_time / nb_delayed

    estimators = {
        "rf": RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "xgb": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=pos_weight,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }

    models = {}
    for model_type, estimator in estimators.items():
        model_name = f"{model_type}_{run_stamp}"
        pipeline = Pipeline([
            ("preprocessing", clone(preprocessor)),
            ("model", estimator),
        ])
        start = time.time()
        pipeline.fit(X_train, y_train)
        duration = time.time() - start
        models[model_name] = (model_type, pipeline, duration)
        print(f"  + {model_name} trained in {duration:.1f} s")
    return models


# Evaluate the models
def evaluate_models(models, X_test, y_test):
    """ Score each model on the test set (threshold 0.5 on the delay probability).
        @return dict {model_name: scores}
    """
    results = {}
    print(f"Reference (always 'on time') : recall 0.000, {y_test.mean():.1%} of test flights delayed")
    for model_name, (model_type, pipeline, duration) in models.items():
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        scores = {
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, y_proba)),
        }
        results[model_name] = scores
        print(f"  {model_name} : TP {tp}  FP {fp}  TN {tn}  FN {fn}  | "
              f"precision {scores['precision']:.3f}  recall {scores['recall']:.3f}  "
              f"F1 {scores['f1']:.3f}  AUC {scores['roc_auc']:.3f}")
    return results


# Save the models
def save_models(models, models_dir):
    """ Save each fitted pipeline (preprocessing + model) with joblib.
        @param models_dir : folder (created if missing)
        @return dict {model_name: file path}
    """
    models_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for model_name, (model_type, pipeline, duration) in models.items():
        path = models_dir / f"{model_name}.joblib"
        joblib.dump(pipeline, path)
        paths[model_name] = str(path)
        print(f"  + {model_name} saved to {path} ({path.stat().st_size / 1e6:.1f} MB)")
    return paths


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

        # Train the models
        run_stamp = datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y%m%d_%H%M")
        models = train_models(X_train, y_train, preprocessor, run_stamp)

        # Evaluate the models
        scores = evaluate_models(models, X_test, y_test)

        # Save the models
        paths = save_models(models, MODELS_DIR)

        print("Training finished")
        sys.exit(0)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)