import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set")
    return create_engine(database_url)


def get_demographics_engine() -> Engine:
    demographics_url = os.getenv("DEMOGRAPHICS_URL")
    if not demographics_url:
        raise ValueError("DEMOGRAPHICS_URL is not set")
    return create_engine(demographics_url)


def get_warehouse_engine() -> Engine:
    warehouse_url = os.getenv("WAREHOUSE_DATABASE_URL")
    if not warehouse_url:
        raise ValueError("WAREHOUSE_DATABASE_URL is not set")
    return create_engine(warehouse_url)


@contextmanager
def get_connection():
    engine = get_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
        engine.dispose()


@contextmanager
def get_demographics_connection():
    engine = get_demographics_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
        engine.dispose()


@contextmanager
def get_warehouse_connection():
    engine = get_warehouse_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
        engine.dispose()
