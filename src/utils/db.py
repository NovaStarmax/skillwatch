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
