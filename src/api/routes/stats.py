from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from src.api.core.security import get_current_user
from src.utils.db import get_warehouse_engine

router = APIRouter()


@router.get(
    "",
    summary="Statistiques développeurs Stack Overflow",
    description="""Retourne l'évolution de l'usage des skills
    chez les développeurs (Stack Overflow 2021-2025,
    traité via Apache Spark).""",
    responses={401: {"description": "Token JWT manquant ou invalide"}},
)
def get_stats(
    skill: Optional[str] = Query(None, description="Filtrer par skill (ex: Python)"),
    _: dict = Depends(get_current_user),
):
    if skill:
        query = """
            SELECT sk.skill_name AS name, sk.category,
                   ss.survey_year AS year, ss.usage_count,
                   ROUND(ss.avg_salary_usd) as avg_salary_usd
            FROM marts.stackoverflow_skills ss
            JOIN marts.skills sk ON sk.skill_name = ss.canonical_skill
            WHERE ss.canonical_skill ILIKE :skill
            ORDER BY ss.survey_year
        """
        params = {"skill": skill}
    else:
        query = """
            SELECT sk.skill_name AS name, sk.category,
                   ss.survey_year AS year, ss.usage_count,
                   ROUND(ss.avg_salary_usd) as avg_salary_usd
            FROM marts.stackoverflow_skills ss
            JOIN marts.skills sk ON sk.skill_name = ss.canonical_skill
            WHERE ss.survey_year = 2025
            ORDER BY ss.usage_count DESC
            LIMIT 50
        """
        params = {}

    with get_warehouse_engine().connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [dict(row._mapping) for row in rows]
