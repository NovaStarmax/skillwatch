from datetime import datetime

from airflow.sdk import dag, task
from airflow.providers.standard.operators.bash import BashOperator

from common import DBT_PROJECT_DIR


@dag(
    dag_id="dbt_departments_smoke_test",
    description="DAG trivial — valide la plomberie Airflow -> dbt -> warehouse",
    schedule=None,        # pas de planification automatique, déclenchement manuel uniquement
    start_date=datetime(2026, 1, 1),
    catchup=False,        # ne pas rattraper de runs passés
    tags=["smoke-test"],
)
def dbt_departments_smoke_test():
    BashOperator(
        task_id="dbt_build_departments",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt build --select departments",
    )


dbt_departments_smoke_test()