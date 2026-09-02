from datetime import datetime

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
DBT_PROJECT_DIR = "/opt/airflow/project/dbt_skillwatch"


@dag(
    dag_id="stackoverflow_archive_pipeline",
    description="Extraction Stack Overflow (archive 2021-2024, Spark) -> dbt",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["source:stackoverflow-archive"],
)
def stackoverflow_archive_pipeline():
    extract = BashOperator(
        task_id="extract_stackoverflow_archive",
        bash_command=f"cd {PROJECT_DIR} && python -m src.extract.stackoverflow_spark",
    )

    dbt_build = BashOperator(
        task_id="dbt_build_stackoverflow_archive",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && dbt build --select "
            "stg_stackoverflow_archive int_stackoverflow_archive_skills"
        ),
    )

    extract >> dbt_build


stackoverflow_archive_pipeline()
