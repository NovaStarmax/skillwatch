from sqlalchemy import text

from src.api.schemas.trainings import Training
from src.utils.db import get_engine

_TRAINING_SELECT = """
    SELECT t.title, t.domain, t.level,
           t.duration_months, t.provider, t.url
    FROM trainings t
"""


def _row_to_training(r) -> Training:
    return Training(
        title=r[0], domain=r[1] or "", level=r[2] or "",
        duration_months=r[3], provider=r[4] or "", url=r[5],
    )


def list_trainings() -> list[Training]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(_TRAINING_SELECT + " ORDER BY t.domain, t.title")
        ).fetchall()
    return [_row_to_training(r) for r in rows]


def trainings_by_skill(skill_name: str) -> list[Training]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT t.title, t.domain, t.level,
                       t.duration_months, t.provider, t.url
                FROM trainings t
                JOIN training_skills ts ON ts.training_id = t.id
                JOIN skills s ON s.id = ts.skill_id
                WHERE s.name ILIKE :skill_name
                ORDER BY t.domain
            """),
            {"skill_name": skill_name},
        ).fetchall()
    return [_row_to_training(r) for r in rows]
