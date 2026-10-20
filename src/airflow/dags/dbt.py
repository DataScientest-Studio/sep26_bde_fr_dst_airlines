from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="airline_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["airline", "spark", "dbt"],
) as dag:


    # ==========================================================
    # Silver : dbt run
    # ==========================================================
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        docker compose \
        -f /home/airline/repos/docker-compose.yaml \
        --profile tools \
        run --rm dbt dbt run
        """,
    )
    

    # ==========================================================
    # Tests Silver/Gold
    # ==========================================================
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="""
        docker compose \
        -f /home/airline/repos/docker-compose.yaml \
        --profile tools \
        run --rm dbt dbt test
        """,
    )

    # ==========================================================
    # Documentation
    # ==========================================================
    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command="""
        docker compose \
        -f /home/airline/repos/docker-compose.yaml \
        --profile tools \
        run --rm dbt dbt docs generate
        """,
        trigger_rule="all_done",
    )

    dbt_run >> dbt_test >> dbt_docs