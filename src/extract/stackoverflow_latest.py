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

DATA_DIR = ROOT / "data" / "raw" / "stackoverflow_latest"
RAW_TABLE = "raw_stackoverflow_latest"


def find_csv(logger) -> Path:
    csvs = list(DATA_DIR.glob("*.csv"))
    if not csvs:
        logger.error(f"[STACKOVERFLOW] Aucun fichier CSV trouvé dans {DATA_DIR}")
        sys.exit(1)
    return csvs[0]


def run() -> None:
    logger = get_logger("stackoverflow")

    # Lecture CSV
    csv_path = find_csv(logger)
    logger.info(f"[STACKOVERFLOW] Lecture {csv_path.name}...")
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    logger.info(f"[STACKOVERFLOW] {len(df)} répondants chargés")

    # === RAW LAYER : chargement quasi brut du CSV, sans matching ni agrégation ===
    # Ces étapes seront réécrites en dbt (staging/intermediate) à partir de cette table raw.
    # Écrit dans skillwatch_warehouse (WAREHOUSE_DATABASE_URL).
    warehouse_engine = get_warehouse_engine()
    df_raw = df.copy()
    df_raw["loaded_at"] = datetime.now(timezone.utc)
    replace_raw_table(warehouse_engine, RAW_TABLE, df_raw)
    logger.info(f"[STACKOVERFLOW] {len(df_raw)} lignes chargées dans {RAW_TABLE} (raw, skillwatch_warehouse)")
    # === FIN RAW LAYER ===


if __name__ == "__main__":
    run()
