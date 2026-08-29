import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_warehouse_engine, replace_raw_table
from src.utils.logger import get_logger

load_dotenv()

SKILLS_MAPPING_PATH = ROOT / "config" / "skills_mapping.json"
RAW_TABLE = "raw_france_travail"
MATCHED_TABLE = "raw_france_travail_skills_matched"


def run() -> None:
    logger = get_logger("match_skills_france_travail")

    try:
        warehouse_engine = get_warehouse_engine()
        warehouse_engine.connect().close()
    except Exception as e:
        logger.error(f"[MATCH FT] WAREHOUSE_DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    with open(SKILLS_MAPPING_PATH, encoding="utf-8") as f:
        mapping: dict[str, str] = json.load(f)

    df = pd.read_sql_table(RAW_TABLE, warehouse_engine)
    logger.info(f"[MATCH FT] {len(df)} offres chargées depuis {RAW_TABLE}")

    rows = []
    skills_matched = 0
    unmatched_count = 0

    for _, offer in df.iterrows():
        external_id = offer["external_id"]
        title = offer.get("title") or ""
        description = offer.get("description") or ""

        # Reproduction exacte de l'algorithme de matching legacy (france_travail.py)
        offer_text = f"{title} {description}".lower()
        offer_tokens = set(re.split(r'[\s\-/;,.()\[\]]+', offer_text))
        matched: list[str] = []
        for alias, canonical in mapping.items():
            hit = alias in offer_tokens if " " not in alias else alias in offer_text
            if hit and canonical not in matched:
                matched.append(canonical)

        if matched:
            for canonical in matched:
                rows.append({"external_id": external_id, "canonical_skill": canonical})
                skills_matched += 1
        else:
            unmatched_count += 1

    df_matched = pd.DataFrame(rows, columns=["external_id", "canonical_skill"])
    df_matched["loaded_at"] = datetime.now(timezone.utc)
    replace_raw_table(warehouse_engine, MATCHED_TABLE, df_matched)
    logger.info(
        f"[MATCH FT] {len(df_matched)} liaisons (external_id, canonical_skill) chargées dans {MATCHED_TABLE}"
    )
    logger.info(
        f"[MATCH FT] {skills_matched} skills matchés | {unmatched_count} offres sans skill matché"
    )


if __name__ == "__main__":
    run()
