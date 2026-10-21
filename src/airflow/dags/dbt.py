from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

with DAG(
    dag_id="airline_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="30 8,14 * * *",
    catchup=False,
    tags=["airline", "spark", "dbt"],
) as dag:


    # ==========================================================
    # Silver/Gold : dbt seed
    # ==========================================================
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command="""
        docker compose \
        -f /home/airline/repos/docker-compose.yaml \
        --profile tools \
        run --rm dbt \
        bash -c "dbt deps && dbt seed"
        """,
    )

    # ==========================================================
    # Silver/Gold : dbt run
    # ==========================================================
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="""
        docker compose \
        -f /home/airline/repos/docker-compose.yaml \
        --profile tools \
        run --rm dbt \
        bash -c "dbt deps && dbt run"
        """,
        trigger_rule=TriggerRule.ALL_DONE
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
        run --rm dbt \
                bash -c "dbt deps && dbt test"
        """,
        trigger_rule=TriggerRule.ALL_DONE
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
        run --rm dbt \
        bash -c "dbt deps && dbt docs generate"
        """,
        trigger_rule="all_done",
    )

    dbt_seed >> dbt_run >> dbt_test >> dbt_docs