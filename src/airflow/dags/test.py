from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="test",
    start_date=datetime(2026, 10, 19),
    schedule=None,
    catchup=False,
) as dag:

    BashOperator(
        task_id="test",
        bash_command="sleep 5 && echo hello"
    )