####################################################
# Run Load Airlabs Schedule from files
# version : 2026.10.16 - rev1
####################################################
from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
    dag_id="ingest_airlabs_schedule",
    start_date=datetime(2026, 10, 16),
    schedule="@daily",
    catchup=False,
    tags=["airlabs"],
) as dag:

    run_ingestion = BashOperator(
        task_id="run_airlabs_ingestion",
        bash_command="""
        docker exec spark \
            python /app/src/notebooks/ingestion/load_airlabs_schedule_files.py
        """
    )