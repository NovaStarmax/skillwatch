from datetime import datetime

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

from common import PROJECT_DIR, DBT_PROJECT_DIR


@dag(
    dag_id="stackoverflow_latest_pipeline",
    description="Extraction Stack Overflow (CSV latest) -> dbt (staging/intermediate)",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["source:stackoverflow-latest"],
)
def stackoverflow_latest_pipeline():
    extract = BashOperator(
        task_id="extract_stackoverflow_latest",
        bash_command=f"cd {PROJECT_DIR} && python -m src.extract.stackoverflow_latest",
    )

    dbt_build = BashOperator(
        task_id="dbt_build_stackoverflow_latest",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && dbt build --select "
            "stg_stackoverflow_latest int_stackoverflow_skills"
        ),
    )

    extract >> dbt_build


stackoverflow_latest_pipeline()
