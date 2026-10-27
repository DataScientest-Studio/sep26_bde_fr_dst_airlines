#!/usr/bin/env python
# coding: utf-8
"""
Deploy a trained model chosen by a human (launched by hand).

Steps:
  1. Read config and secrets (shared config.json of the ingestion folder)
  2. Check that the model exists in RESULTS_TABLE and on disk
  3. Copy it to MODELS_DIR/model.joblib, the file loaded by the API
  4. Set deployed_at for this model and clear it for the previous one

Usage:
  spark-submit deploy_model.py <model_name>      e.g. xgb_20261027_1453
The API loads the model at startup: restart it after a deployment.
"""
from pathlib import Path
import os, sys
import argparse
import shutil
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from common import Config
from sqlalchemy import create_engine, text

is_local = os.getenv("RUN_ENV") != "docker"

CONFIG_FILE = str(Path(__file__).resolve().parent.parent / "ingestion" / "config.json")
MODELS_DIR = Path("/app/workspace/models")
DEPLOYED_FILE = "model.joblib"
RESULTS_TABLE = "ml.model_runs"


# Check that the model exists in the results table and on disk
def check_model(engine, table, model_name):
    """ @return path of the model file """
    with engine.connect() as conn:
        row = conn.execute(
            text(f"select model_path from {table} where model_name = :name"),
            {"name": model_name},
        ).fetchone()
    if row is None:
        raise Exception(f"{model_name} not found in {table}")
    path = Path(row[0])
    if not path.is_file():
        raise Exception(f"{model_name} file not found : {path}")
    print(f"{model_name} found : {path}")
    return path


# Copy the model to the file loaded by the API
def copy_model(path, models_dir, deployed_file):
    """ Copy to a temporary file then rename, so the API never reads a half-copied file """
    target = models_dir / deployed_file
    tmp = models_dir / f"{deployed_file}.tmp"
    shutil.copy2(path, tmp)
    os.replace(tmp, target)
    print(f"{path.name} copied to {target}")
    return target


# Mark the deployed model in the results table
def mark_deployed(engine, table, model_name, deployed_at):
    """ Only one model has deployed_at set: the one currently used by the API """
    with engine.begin() as conn:
        conn.execute(text(f"update {table} set deployed_at = null where deployed_at is not null"))
        conn.execute(
            text(f"update {table} set deployed_at = :deployed_at where model_name = :name"),
            {"deployed_at": deployed_at, "name": model_name},
        )
    print(f"{model_name} marked as deployed in {table} ({deployed_at:%Y-%m-%d %H:%M} UTC)")


# Entry point
if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Deploy a trained model")
        parser.add_argument("model_name", help="Model to deploy, e.g. xgb_20261027_1453")
        args = parser.parse_args()

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

        engine = create_engine(
            f"postgresql+psycopg2://{PG_USER}:{password}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        )

        # Check the model
        path = check_model(engine, RESULTS_TABLE, args.model_name)

        # Copy it for the API
        copy_model(path, MODELS_DIR, DEPLOYED_FILE)

        # Mark it as deployed
        mark_deployed(engine, RESULTS_TABLE, args.model_name, datetime.now(timezone.utc))

        print("Deployment finished : restart the API to load the new model")
        sys.exit(0)
    except Exception as e:
        print(f"Error : {e}")
        sys.exit(1)