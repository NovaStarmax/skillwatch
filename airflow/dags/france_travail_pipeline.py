from datetime import datetime, timedelta

from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

from common import PROJECT_DIR, DBT_PROJECT_DIR

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


@dag(
    dag_id="france_travail_pipeline",
    description="Extraction France Travail (API live) -> matching skills -> dbt",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["source:france-travail"],
)
def france_travail_pipeline():
    extract = BashOperator(
        task_id="extract_france_travail",
        bash_command=f"cd {PROJECT_DIR} && python -m src.extract.france_travail",
        retries=3,
        retry_delay=timedelta(minutes=1),
    )

    match_skills = BashOperator(
        task_id="match_skills_france_travail",
        bash_command=f"cd {PROJECT_DIR} && python -m src.extract.match_skills_france_travail",
    )

    dbt_build = BashOperator(
        task_id="dbt_build_france_travail",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && dbt build --select "
            "stg_france_travail stg_france_travail_skills "
            "int_france_travail_offers job_offers job_offer_skills"
        ),
    )

    extract >> match_skills >> dbt_build


france_travail_pipeline()