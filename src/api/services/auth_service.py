import logging

from sqlalchemy import text

from src.api.core.config import ADMIN_PASSWORD, ADMIN_USERNAME
from src.api.core.security import hash_password, verify_password
from src.utils.db import get_engine

logger = logging.getLogger(__name__)


def authenticate_user(username: str, password: str) -> dict | None:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, hashed_password FROM users WHERE username = :u"),
            {"u": username},
        ).fetchone()
    if not row or not verify_password(password, row[2]):
        return None
    return {"id": row[0], "username": row[1]}


def create_default_admin() -> None:
    if not ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD non défini — création du compte admin ignorée")
        return
    engine = get_engine()
    hashed = hash_password(ADMIN_PASSWORD)
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO users (username, hashed_password)
                VALUES (:username, :hashed_password)
                ON CONFLICT (username) DO NOTHING
            """),
            {"username": ADMIN_USERNAME, "hashed_password": hashed},
        )
        conn.commit()
