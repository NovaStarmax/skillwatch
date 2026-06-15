import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_demographics_engine
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger("demographics")


def _engine():
    try:
        engine = get_demographics_engine()
        engine.connect().close()
        logger.info("[DEMOGRAPHICS] Connexion demographics_db OK")
        return engine
    except Exception as e:
        logger.error(f"[DEMOGRAPHICS] DEMOGRAPHICS_URL inaccessible: {e}")
        sys.exit(1)


def get_all_departments() -> list[dict]:
    with _engine().connect() as conn:
        rows = conn.execute(
            text("SELECT dep, nom, population FROM departments ORDER BY population DESC")
        ).fetchall()
    if not rows:
        logger.warning("[DEMOGRAPHICS] Table departments vide")
        return []
    logger.info(f"[DEMOGRAPHICS] {len(rows)} départements extraits")
    return [{"dep": r[0], "nom": r[1], "population": r[2]} for r in rows]


def get_department(dept_code: str) -> dict | None:
    with _engine().connect() as conn:
        row = conn.execute(
            text("SELECT dep, nom, population FROM departments WHERE dep = :dept_code"),
            {"dept_code": dept_code},
        ).fetchone()
    if row is None:
        return None
    return {"dep": row[0], "nom": row[1], "population": row[2]}


def get_top_departments(limit: int = 10) -> list[dict]:
    with _engine().connect() as conn:
        rows = conn.execute(
            text(
                "SELECT dep, nom, population FROM departments "
                "ORDER BY population DESC LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()
    if not rows:
        logger.warning("[DEMOGRAPHICS] Table departments vide")
        return []
    logger.info(f"[DEMOGRAPHICS] Top {limit} départements par population")
    return [{"dep": r[0], "nom": r[1], "population": r[2]} for r in rows]


def get_departments_stats() -> dict:
    with _engine().connect() as conn:
        row = conn.execute(
            text("""
                SELECT
                    COUNT(*)          AS total,
                    SUM(population)   AS population_totale,
                    AVG(population)   AS population_moyenne,
                    MAX(population)   AS population_max,
                    MIN(population)   AS population_min
                FROM departments
            """)
        ).fetchone()
    stats = {
        "total": row[0],
        "total_population": row[1],
        "avg_population": round(float(row[2]), 0) if row[2] else None,
        "max_population": row[3],
        "min_population": row[4],
    }
    total_M = round(stats["total_population"] / 1_000_000, 1) if stats["total_population"] else 0
    avg_k = round(stats["avg_population"] / 1_000, 0) if stats["avg_population"] else 0
    logger.info(
        f"[DEMOGRAPHICS] Stats: {stats['total']} depts | "
        f"total_population: {total_M}M | avg: {avg_k:.0f}k"
    )
    return stats


def run() -> None:
    departments = get_all_departments()
    top = get_top_departments(limit=10)
    dept = get_department("75")
    stats = get_departments_stats()

    print(f"\nTotal départements : {len(departments)}")
    print(f"\nTop 10 par population :")
    for d in top:
        print(f"  {d['dep']} — {d['nom']} : {d['population']:,}")
    print(f"\nDépartement 75 : {dept}")
    print(f"\nStats globales : {stats}")


if __name__ == "__main__":
    run()
