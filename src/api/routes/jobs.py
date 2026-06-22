from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from src.api.core.security import get_current_user
from src.utils.db import get_engine

router = APIRouter()


@router.get(
    "",
    summary="Liste les offres d'emploi",
    description="""Retourne les offres d'emploi collectées
    depuis France Travail. Filtres optionnels par skill
    et par département.""",
    responses={401: {"description": "Token JWT manquant ou invalide"}},
)
def get_jobs(
    skill: Optional[str] = Query(None, description="Filtrer par skill (ex: Python)"),
    dept_code: Optional[str] = Query(None, description="Filtrer par département (ex: 75)"),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    query = """
        SELECT DISTINCT jo.external_id, jo.title, jo.company,
               jo.location, jo.dept_code, jo.dept_population,
               jo.salary_min, jo.salary_max,
               jo.contract_type, jo.source, jo.published_at
        FROM job_offers jo
    """
    params = {"limit": limit}

    if skill:
        query += """
        JOIN job_offer_skills jos ON jo.id = jos.job_offer_id
        JOIN skills s ON s.id = jos.skill_id
        WHERE s.name ILIKE :skill
        """
        params["skill"] = skill

    if dept_code:
        if skill:
            query += " AND jo.dept_code = :dept_code"
        else:
            query += " WHERE jo.dept_code = :dept_code"
        params["dept_code"] = dept_code

    query += " ORDER BY jo.published_at DESC NULLS LAST LIMIT :limit"

    with get_engine().connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [dict(row._mapping) for row in rows]
