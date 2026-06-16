import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logger import get_logger

load_dotenv()


def run() -> None:
    logger = get_logger("transform")
    logger.info("[TRANSFORM] Calcul market_summary en cours...")
    start = time.time()

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_summary (
                skill_id INTEGER PRIMARY KEY REFERENCES skills(id) ON DELETE CASCADE,
                job_offer_count INTEGER DEFAULT 0,
                developer_usage_count INTEGER DEFAULT 0,
                avg_salary_eur NUMERIC,
                training_count INTEGER DEFAULT 0,
                computed_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()

        skills = conn.execute(text("SELECT id, name FROM skills ORDER BY name")).fetchall()
        count = 0
        job_counts = []

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

            conn.execute(
                text("""
                    INSERT INTO market_summary (
                        skill_id, job_offer_count, developer_usage_count,
                        avg_salary_eur, training_count, computed_at
                    )
                    VALUES (
                        :skill_id, :job_offer_count, :developer_usage_count,
                        :avg_salary_eur, :training_count, NOW()
                    )
                    ON CONFLICT (skill_id) DO UPDATE SET
                        job_offer_count = EXCLUDED.job_offer_count,
                        developer_usage_count = EXCLUDED.developer_usage_count,
                        avg_salary_eur = EXCLUDED.avg_salary_eur,
                        training_count = EXCLUDED.training_count,
                        computed_at = NOW()
                """),
                {
                    "skill_id": skill_id,
                    "job_offer_count": job_offer_count,
                    "developer_usage_count": developer_usage_count,
                    "avg_salary_eur": avg_salary_eur,
                    "training_count": training_count,
                },
            )

            count += 1
            job_counts.append((skill_name, job_offer_count))

        conn.commit()

    job_counts.sort(key=lambda x: x[1], reverse=True)
    top5 = ", ".join(f"{name}({cnt})" for name, cnt in job_counts[:5])
    duration = round(time.time() - start, 1)
    logger.info(f"[TRANSFORM] {count} skills traités")
    logger.info(f"[TRANSFORM] Top 5 skills demandés: {top5}")
    logger.info(f"[TRANSFORM] Terminé | durée: {duration}s")


if __name__ == "__main__":
    run()
