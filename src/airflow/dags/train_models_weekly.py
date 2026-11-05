####################################################
# Train delay prediction models every week
# version : 2026.11.05 - rev1
####################################################
from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="train_models_weekly",
    start_date=datetime(2026, 11, 5),
    schedule="0 10 * * 5",
    catchup=False,
    tags=["ml"],
) as dag:

    run_training = BashOperator(
        task_id="run_train_models",
        bash_command="""
        docker exec spark \
        /opt/spark/bin/spark-submit \
        /app/src/notebooks/ml/train_models.py
        """,
    )