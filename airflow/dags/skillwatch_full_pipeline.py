from datetime import datetime, timedelta

from airflow.sdk import dag, task_group
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"
DBT_PROJECT_DIR = "/opt/airflow/project/dbt_skillwatch"

default_args = {"retries": 2, "retry_delay": timedelta(minutes=2)}


@dag(
    dag_id="skillwatch_full_pipeline",
    description="Pipeline complet : 4 sources en parallèle -> dbt build consolidé (skills, market_summary inclus)",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["full-pipeline"],
)
def skillwatch_full_pipeline():

    @task_group(group_id="openclassrooms")
    def openclassrooms():
        BashOperator(
            task_id="extract",
            bash_command=f"cd {PROJECT_DIR} && python -m src.extract.openclassrooms",
        )

    @task_group(group_id="stackoverflow_latest")
    def stackoverflow_latest():
        BashOperator(
            task_id="extract",
            bash_command=f"cd {PROJECT_DIR} && python -m src.extract.stackoverflow_latest",
        )

    @task_group(group_id="stackoverflow_archive")
    def stackoverflow_archive():
        BashOperator(
            task_id="extract",
            bash_command=f"cd {PROJECT_DIR} && python -m src.extract.stackoverflow_spark",
        )

    @task_group(group_id="france_travail")
    def france_travail():
        extract = BashOperator(
            task_id="extract",
            bash_command=f"cd {PROJECT_DIR} && python -m src.extract.france_travail",
            retries=3,
            retry_delay=timedelta(minutes=1),
        )
        match_skills = BashOperator(
            task_id="match_skills",
            bash_command=f"cd {PROJECT_DIR} && python -m src.extract.match_skills_france_travail",
        )
        extract >> match_skills

    dbt_build_all = BashOperator(
        task_id="dbt_build_all",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt build",
    )

    [
        openclassrooms(),
        stackoverflow_latest(),
        stackoverflow_archive(),
        france_travail(),
    ] >> dbt_build_all


skillwatch_full_pipeline()
