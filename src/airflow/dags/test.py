from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

test = BashOperator(
    task_id="test",
    bash_command="echo hello"
)