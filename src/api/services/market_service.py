from sqlalchemy import text

from src.api.schemas.market import DepartmentStats, MarketSummaryItem
from src.utils.db import get_demographics_engine, get_engine


def market_summary() -> list[MarketSummaryItem]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT s.name, s.category,
                   ms.job_offer_count, ms.developer_usage_count,
                   ms.avg_salary_eur, ms.training_count
            FROM market_summary ms
            JOIN skills s ON s.id = ms.skill_id
            WHERE ms.job_offer_count > 0
            ORDER BY ms.job_offer_count DESC
            LIMIT 20
        """)).fetchall()
    return [
        MarketSummaryItem(
            skill=r[0], category=r[1] or "",
            job_offer_count=r[2], developer_usage_count=r[3],
            avg_salary_eur=float(r[4]) if r[4] is not None else None,
            training_count=r[5],
        )
        for r in rows
    ]


def by_department() -> list[DepartmentStats]:
    warehouse_engine = get_engine()
    with warehouse_engine.connect() as conn:
        job_rows = conn.execute(text("""
            SELECT dept_code, COUNT(*) AS job_count
            FROM job_offers
            WHERE dept_code IS NOT NULL
            GROUP BY dept_code
            ORDER BY job_count DESC
            LIMIT 20
        """)).fetchall()

    demo_engine = get_demographics_engine()
    with demo_engine.connect() as conn:
        dept_rows = conn.execute(text("""
            SELECT dep, nom, population
            FROM departments
            WHERE population IS NOT NULL AND population > 0
        """)).fetchall()

    dept_map = {r[0]: (r[1], r[2]) for r in dept_rows}

    result = []
    for row in job_rows:
        dept_code, job_count = row[0], int(row[1])
        if dept_code in dept_map:
            dept_name, population = dept_map[dept_code]
            result.append(DepartmentStats(
                dept_code=dept_code,
                dept_name=dept_name,
                population=population,
                job_count=job_count,
                jobs_per_million_hab=round(job_count * 1_000_000 / population, 2),
            ))
    return result
