####################################################
# Run Load Airlabs Schedule from files
# version : 2026.10.16
####################################################
from airflow.operators.bash import BashOperator

run_ingestion = BashOperator(
    task_id="run_airlabs_ingestion",
    bash_command="""
    docker exec spark \
      python /app/src/notebooks/ingestion/load_airlabs_schedule_files.py
    """
)