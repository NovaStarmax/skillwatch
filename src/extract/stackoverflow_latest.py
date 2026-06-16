import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logger import get_logger

load_dotenv()

SURVEY_YEAR = 2025
DATA_DIR = ROOT / "data" / "raw" / "stackoverflow_latest"
SKILLS_MAPPING_PATH = ROOT / "config" / "skills_mapping.json"
UNMATCHED_LOG = ROOT / "data" / "unmatched.log"

SKILL_COLUMNS = [
    "LanguageHaveWorkedWith",
    "DatabaseHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "WebframeHaveWorkedWith",
    "MiscTechHaveWorkedWith",
]


def find_csv(logger) -> Path:
    csvs = list(DATA_DIR.glob("*.csv"))
    if not csvs:
        logger.error(f"[STACKOVERFLOW] Aucun fichier CSV trouvé dans {DATA_DIR}")
        sys.exit(1)
    return csvs[0]


def load_mapping() -> dict[str, str]:
    with open(SKILLS_MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


def run() -> None:
    logger = get_logger("stackoverflow")

    # Connexion warehouse
    try:
        engine = get_engine()
        engine.connect().close()
    except Exception as e:
        logger.error(f"[STACKOVERFLOW] DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    # Lecture CSV
    csv_path = find_csv(logger)
    logger.info(f"[STACKOVERFLOW] Lecture {csv_path.name}...")
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    logger.info(f"[STACKOVERFLOW] {len(df)} répondants chargés")

    mapping = load_mapping()

    # skill_name -> set d'index répondants
    skill_respondents: dict[str, set[int]] = defaultdict(set)
    unmatched_seen: set[str] = set()
    unmatched_count = 0

    UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)

    for col in SKILL_COLUMNS:
        if col not in df.columns:
            logger.warning(f"[STACKOVERFLOW] Colonne absente dans le CSV: {col} → skip")
            continue

        for idx, raw_val in df[col].dropna().items():
            row_tokens = {t.strip().lower() for t in str(raw_val).split(";") if t.strip()}
            for alias, canonical in mapping.items():
                if alias in row_tokens:
                    skill_respondents[canonical].add(idx)
            for token in row_tokens:
                if token not in mapping and token not in unmatched_seen:
                    unmatched_seen.add(token)
                    with open(UNMATCHED_LOG, "a", encoding="utf-8") as f:
                        f.write(
                            f"[UNMATCHED] source: stackoverflow | col: {col} | value: {token}\n"
                        )
                    unmatched_count += 1

    logger.info(f"[STACKOVERFLOW] {len(skill_respondents)} skills uniques détectés")

    # Top 5
    top5 = sorted(skill_respondents.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    top5_str = ", ".join(f"{name}({len(idxs)})" for name, idxs in top5)
    logger.info(f"[STACKOVERFLOW] Top 5: {top5_str}")
    logger.info(f"[STACKOVERFLOW] {unmatched_count} non-matchés → data/unmatched.log")

    # Agrégation salary
    salary_series = pd.to_numeric(df.get("ConvertedCompYearly"), errors="coerce")

    # Upsert
    start = time.time()
    with engine.connect() as conn:
        for skill_name, respondent_ids in skill_respondents.items():
            usage_count = len(respondent_ids)

            valid_salaries = salary_series.loc[list(respondent_ids)].dropna()
            avg_salary = round(float(valid_salaries.mean()), 2) if not valid_salaries.empty else None

            # Upsert skill
            conn.execute(
                text("""
                    INSERT INTO skills (name, category)
                    VALUES (:name, 'unknown')
                    ON CONFLICT (name) DO NOTHING
                """),
                {"name": skill_name},
            )
            row = conn.execute(
                text("SELECT id FROM skills WHERE name = :name"),
                {"name": skill_name},
            ).fetchone()
            if not row:
                continue
            skill_id = row[0]

            # Upsert survey_stats
            conn.execute(
                text("""
                    INSERT INTO survey_stats (skill_id, year, usage_count, avg_salary_usd)
                    VALUES (:skill_id, :year, :usage_count, :avg_salary_usd)
                    ON CONFLICT (skill_id, year) DO UPDATE SET
                        usage_count = EXCLUDED.usage_count,
                        avg_salary_usd = EXCLUDED.avg_salary_usd
                """),
                {
                    "skill_id": skill_id,
                    "year": SURVEY_YEAR,
                    "usage_count": usage_count,
                    "avg_salary_usd": avg_salary,
                },
            )

        conn.commit()

    duration = round(time.time() - start, 1)
    logger.info(
        f"[STACKOVERFLOW] Upsert survey_stats terminé | année: {SURVEY_YEAR} | durée: {duration}s"
    )


if __name__ == "__main__":
    run()
