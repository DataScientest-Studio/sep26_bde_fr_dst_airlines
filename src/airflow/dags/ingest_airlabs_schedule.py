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
    schedule="30 8,14,20 * * *",
    catchup=False,
    tags=["airlabs"],
) as dag:

    run_ingestion = BashOperator(
        task_id="run_airlabs_ingestion",
        bash_command="""
        docker exec spark \
        /opt/spark/bin/spark-submit \
        --jars /opt/spark-extra-jars/gcs-connector.jar,/opt/spark-extra-jars/postgresql.jar \
        /app/src/notebooks/ingestion/load_airlabs_schedule_files.py
        """
          )
    
    run_meteo = BashOperator(
        task_id="run_meteo_collect",
        bash_command="""
        docker exec spark \
        /opt/spark/bin/spark-submit \
        --jars /opt/spark-extra-jars/gcs-connector.jar,/opt/spark-extra-jars/postgresql.jar \
        /app/src/notebooks/ingestion/collect_meteo_airlabs.py
        """,
    )
  
    run_ingestion >> run_meteo
  