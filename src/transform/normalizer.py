import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_demographics_engine, get_engine
from src.utils.logger import get_logger

load_dotenv()


def run() -> None:
    logger = get_logger("transform")
    logger.info("[TRANSFORM] Calcul market_summary en cours...")
    start = time.time()

    engine = get_engine()
    demo_engine = get_demographics_engine()

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_summary (
                skill_id INTEGER PRIMARY KEY REFERENCES skills(id) ON DELETE CASCADE,
                job_offer_count INTEGER DEFAULT 0,
                developer_usage_count INTEGER DEFAULT 0,
                avg_salary_eur NUMERIC,
                training_count INTEGER DEFAULT 0,
                top_dept VARCHAR(10),
                top_dept_name VARCHAR(100),
                top_dept_population INTEGER,
                computed_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

        skills = conn.execute(text("SELECT id, name FROM skills ORDER BY name")).fetchall()
        count = 0
        top_dept_count = 0
        job_counts = []

        with demo_engine.connect() as demo_conn:
            for skill in skills:
                skill_id = skill[0]
                skill_name = skill[1]

                job_offer_count = conn.execute(
                    text("SELECT COUNT(*) FROM job_offer_skills WHERE skill_id = :skill_id"),
                    {"skill_id": skill_id},
                ).scalar()

                row = conn.execute(
                    text("""
                        SELECT usage_count, avg_salary_usd
                        FROM survey_stats
                        WHERE skill_id = :skill_id AND year = 2025
                    """),
                    {"skill_id": skill_id},
                ).fetchone()

                developer_usage_count = row[0] if row else 0
                avg_salary_eur = round(float(row[1]) * 0.92, 2) if row and row[1] else None

                training_count = conn.execute(
                    text("SELECT COUNT(*) FROM training_skills WHERE skill_id = :skill_id"),
                    {"skill_id": skill_id},
                ).scalar()

                # Top département par nombre d'offres pour ce skill
                top_dept = None
                top_dept_name = None
                top_dept_population = None

                if job_offer_count > 0:
                    dept_row = conn.execute(
                        text("""
                            SELECT jo.dept_code, COUNT(*) AS nb_offres
                            FROM job_offers jo
                            JOIN job_offer_skills jos ON jo.id = jos.job_offer_id
                            WHERE jos.skill_id = :skill_id
                              AND jo.dept_code IS NOT NULL
                            GROUP BY jo.dept_code
                            ORDER BY nb_offres DESC
                            LIMIT 1
                        """),
                        {"skill_id": skill_id},
                    ).fetchone()

                    if dept_row:
                        dept_code = dept_row[0]
                        d = demo_conn.execute(
                            text("SELECT nom, population FROM departments WHERE dep = :dept_code"),
                            {"dept_code": dept_code},
                        ).fetchone()
                        if d:
                            top_dept = dept_code
                            top_dept_name = d[0]
                            top_dept_population = d[1]
                            top_dept_count += 1

                conn.execute(
                    text("""
                        INSERT INTO market_summary (
                            skill_id, job_offer_count, developer_usage_count,
                            avg_salary_eur, training_count,
                            top_dept, top_dept_name, top_dept_population,
                            computed_at
                        )
                        VALUES (
                            :skill_id, :job_offer_count, :developer_usage_count,
                            :avg_salary_eur, :training_count,
                            :top_dept, :top_dept_name, :top_dept_population,
                            NOW()
                        )
                        ON CONFLICT (skill_id) DO UPDATE SET
                            job_offer_count = EXCLUDED.job_offer_count,
                            developer_usage_count = EXCLUDED.developer_usage_count,
                            avg_salary_eur = EXCLUDED.avg_salary_eur,
                            training_count = EXCLUDED.training_count,
                            top_dept = EXCLUDED.top_dept,
                            top_dept_name = EXCLUDED.top_dept_name,
                            top_dept_population = EXCLUDED.top_dept_population,
                            computed_at = NOW()
                    """),
                    {
                        "skill_id": skill_id,
                        "job_offer_count": job_offer_count,
                        "developer_usage_count": developer_usage_count,
                        "avg_salary_eur": avg_salary_eur,
                        "training_count": training_count,
                        "top_dept": top_dept,
                        "top_dept_name": top_dept_name,
                        "top_dept_population": top_dept_population,
                    },
                )

                count += 1
                job_counts.append((skill_name, job_offer_count))

        conn.commit()

    job_counts.sort(key=lambda x: x[1], reverse=True)
    top5 = ", ".join(f"{name}({cnt})" for name, cnt in job_counts[:5])
    duration = round(time.time() - start, 1)
    logger.info(f"[TRANSFORM] {count} skills traités")
    logger.info(f"[TRANSFORM] Top dept calculé pour {top_dept_count}/{count} skills")
    logger.info(f"[TRANSFORM] Top 5 skills demandés: {top5}")
    logger.info(f"[TRANSFORM] Terminé | durée: {duration}s")


if __name__ == "__main__":
    run()
