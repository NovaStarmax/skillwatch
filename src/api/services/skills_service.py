from sqlalchemy import text

from src.api.schemas.skills import SkillDetail
from src.utils.db import get_engine

_SKILL_SELECT = """
    SELECT s.name, s.category,
           COALESCE(ms.job_offer_count, 0),
           COALESCE(ms.developer_usage_count, 0),
           ms.avg_salary_eur,
           COALESCE(ms.training_count, 0)
    FROM skills s
    LEFT JOIN market_summary ms ON ms.skill_id = s.id
"""


def _row_to_detail(r) -> SkillDetail:
    return SkillDetail(
        name=r[0],
        category=r[1] or "",
        job_offer_count=r[2],
        developer_usage_count=r[3],
        avg_salary_eur=float(r[4]) if r[4] is not None else None,
        training_count=r[5],
    )


def list_skills() -> list[SkillDetail]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(_SKILL_SELECT + " ORDER BY ms.job_offer_count DESC NULLS LAST")
        ).fetchall()
    return [_row_to_detail(r) for r in rows]


def get_skill_by_name(name: str) -> SkillDetail | None:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(_SKILL_SELECT + " WHERE s.name ILIKE :name ORDER BY ms.job_offer_count DESC NULLS LAST"),
            {"name": name},
        ).fetchall()
    if not rows:
        return None
    return _row_to_detail(rows[0])
