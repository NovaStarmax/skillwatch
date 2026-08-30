import os

import pandas as pd
from psycopg2 import errors as psycopg2_errors
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError


def get_warehouse_engine() -> Engine:
    warehouse_url = os.getenv("WAREHOUSE_DATABASE_URL")
    if not warehouse_url:
        raise ValueError("WAREHOUSE_DATABASE_URL is not set")
    return create_engine(warehouse_url)


def replace_raw_table(engine: Engine, table_name: str, df: pd.DataFrame, schema: str = "raw") -> None:
    """Remplace le contenu d'une table raw dans une seule transaction (TRUNCATE + append),
    contrairement à to_sql(if_exists="replace") qui DROP puis recrée la table hors
    transaction : une requête concurrente ou un `dbt build` lancé entre les deux peut
    alors voir la table absente, et toute vue dbt construite dessus casse (dépendance
    DROPée). TRUNCATE reste dans la même transaction que l'insertion : soit tout est
    visible (ancien contenu jusqu'au commit, puis nouveau), soit rien ne change (rollback).
    Premier run (table absente) : le TRUNCATE échoue en UndefinedTable, on laisse to_sql
    créer la table normalement dans la même transaction. Cible le schéma raw par défaut
    (skillwatch_warehouse.raw.*), séparé de public où vivent les seeds et les modèles dbt.
    """
    with engine.begin() as conn:
        savepoint = conn.begin_nested()
        try:
            conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table_name}"'))
            savepoint.commit()
        except ProgrammingError as e:
            savepoint.rollback()
            if not isinstance(e.orig, psycopg2_errors.UndefinedTable):
                raise
        df.to_sql(
            table_name,
            conn,
            schema=schema,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=5000,
        )

