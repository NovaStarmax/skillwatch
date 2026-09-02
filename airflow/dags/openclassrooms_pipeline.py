from datetime import datetime

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

from common import PROJECT_DIR, DBT_PROJECT_DIR


@dag(
    dag_id="openclassrooms_pipeline",
    description="Extraction OpenClassrooms -> dbt (staging/intermediate/marts)",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["source:openclassrooms"],
)
def openclassrooms_pipeline():
    extract = BashOperator(
        task_id="extract_openclassrooms",
        bash_command=f"cd {PROJECT_DIR} && python -m src.extract.openclassrooms",
    )

    dbt_build = BashOperator(
        task_id="dbt_build_openclassrooms",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && dbt build --select "
            "stg_openclassrooms_trainings stg_openclassrooms_skills "
            "int_openclassrooms_skills trainings training_skills"
        ),
    )

    extract >> dbt_build


openclassrooms_pipeline()
