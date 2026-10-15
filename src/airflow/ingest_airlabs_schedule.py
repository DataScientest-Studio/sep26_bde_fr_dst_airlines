from airflow.operators.bash import BashOperator

run_ingestion = BashOperator(
    task_id="run_airlabs_ingestion",
    bash_command="""
    docker exec spark \
      python /app/src/notebooks/ingestion/load_airlabs_schedule_files.py
    """
)