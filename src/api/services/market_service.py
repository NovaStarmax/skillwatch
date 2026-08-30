from sqlalchemy import text

from src.api.schemas.market import DepartmentStats, MarketSummaryItem
from src.utils.db import get_warehouse_engine


def market_summary() -> list[MarketSummaryItem]:
    engine = get_warehouse_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT sk.skill_name, sk.category,
                   ms.job_offer_count, ms.developer_usage_count,
                   ms.avg_salary_eur, ms.training_count,
                   ms.top_dept, ms.top_dept_name, ms.top_dept_population
            FROM marts.market_summary ms
            JOIN marts.skills sk ON sk.skill_name = ms.skill_name
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
            top_dept=r[6],
            top_dept_name=r[7],
            top_dept_population=int(r[8]) if r[8] is not None else None,
        )
        for r in rows
    ]


def by_department() -> list[DepartmentStats]:
    engine = get_warehouse_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT jo.dept_code, d.nom AS dept_name, d.population, COUNT(*) AS job_count
            FROM marts.job_offers jo
            JOIN public.departments d ON jo.dept_code = d.dep
            WHERE jo.dept_code IS NOT NULL
              AND d.population IS NOT NULL AND d.population > 0
            GROUP BY jo.dept_code, d.nom, d.population
            ORDER BY job_count DESC
            LIMIT 20
        """)).fetchall()

    return [
        DepartmentStats(
            dept_code=r[0],
            dept_name=r[1],
            population=r[2],
            job_count=int(r[3]),
            jobs_per_million_hab=round(int(r[3]) * 1_000_000 / r[2], 2),
        )
        for r in rows
    ]
