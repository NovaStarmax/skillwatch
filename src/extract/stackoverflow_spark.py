import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_warehouse_engine, replace_raw_table
from src.utils.logger import get_logger

load_dotenv()

ARCHIVE_DIR = ROOT / "data" / "raw" / "stackoverflow_archive"
RAW_TABLE = "raw_stackoverflow_archive"

# Colonnes multi-valeurs stables (présentes sur toutes les années)
STABLE_COLS = [
    "LanguageHaveWorkedWith",
    "DatabaseHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "WebframeHaveWorkedWith",
]
# Colonnes optionnelles (absentes certaines années)
OPTIONAL_COLS = [
    "MiscTechHaveWorkedWith",
    "ToolsTechHaveWorkedWith",
]
SALARY_COL = "ConvertedCompYearly"


def extract_year(filename: str) -> int | None:
    import re
    match = re.search(r"(\d{4})", filename)
    return int(match.group(1)) if match else None


def run() -> None:
    logger = get_logger("spark")

    # Vérification dossier archive
    csv_files = sorted(ARCHIVE_DIR.glob("*.csv"))
    if not csv_files:
        logger.error(f"[SPARK] Aucun fichier CSV dans {ARCHIVE_DIR}")
        sys.exit(1)

    # Init SparkSession
    logger.info("[SPARK] Initialisation SparkSession local[*]")
    spark = (
        SparkSession.builder
        .appName("SkillWatch-StackOverflow-Archive")
        .master("local[*]")
        .config("spark.driver.memory", "8g")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    start = time.time()
    raw_frames = []
    total_respondents = 0
    years_loaded = []

    # Lecture fichier par fichier
    for csv_path in csv_files:
        year = extract_year(csv_path.name)
        if year is None:
            logger.warning(f"[SPARK] Impossible d'extraire l'année de {csv_path.name} → skip")
            continue

        try:
            df = spark.read.csv(
                str(csv_path),
                header=True,
                inferSchema=False,
                encoding="UTF-8",
            )
        except Exception as e:
            logger.warning(f"[SPARK] Erreur lecture {csv_path.name}: {e} → skip")
            continue

        df = df.withColumn("survey_year", lit(year))

        # Colonnes disponibles dans ce fichier
        available_cols = set(df.columns)
        skill_cols_found = [c for c in STABLE_COLS + OPTIONAL_COLS if c in available_cols]
        useful_col_count = len(skill_cols_found) + (1 if SALARY_COL in available_cols else 0)

        # === RAW LAYER : capture quasi brute de ce fichier, format large (une ligne par répondant) ===
        raw_frames.append(
            df.select(
                col("ResponseId").alias("response_id"),
                col("survey_year"),
                *[col(c) for c in skill_cols_found],
                col(SALARY_COL).alias("ConvertedCompYearly"),
            )
        )
        # === FIN RAW LAYER (collecte) ===

        n_rows = df.count()
        total_respondents += n_rows
        years_loaded.append(year)
        logger.info(
            f"[SPARK] Fichier: {csv_path.name} | {n_rows} lignes | {useful_col_count} colonnes utiles"
        )

        # Log colonnes optionnelles absentes
        for opt in OPTIONAL_COLS:
            if opt not in available_cols:
                logger.warning(f"[SPARK] Colonne absente dans {csv_path.name}: {opt} → skip colonne")

    logger.info(
        f"[SPARK] Total: {total_respondents} répondants sur {len(years_loaded)} années"
    )

    # === RAW LAYER : union des fichiers + écriture quasi brute dans skillwatch_warehouse ===
    # Une ligne par répondant par année, format large (skills encore délimités par ";"),
    # sans unpivot ni matching. Clé logique : (survey_year, response_id) — response_id
    # repart à 1 chaque année, donc pas de contrainte unique sur response_id seul.
    # Écrit dans skillwatch_warehouse (WAREHOUSE_DATABASE_URL).
    if raw_frames:
        combined_raw = raw_frames[0]
        for frame in raw_frames[1:]:
            combined_raw = combined_raw.union(frame)

        warehouse_engine = get_warehouse_engine()
        df_raw = combined_raw.toPandas()
        df_raw["loaded_at"] = datetime.now(timezone.utc)
        replace_raw_table(warehouse_engine, RAW_TABLE, df_raw)
        logger.info(f"[SPARK] {len(df_raw)} lignes chargées dans {RAW_TABLE} (raw, skillwatch_warehouse)")
    else:
        logger.warning("[SPARK] Aucune donnée à charger dans le raw layer")
    # === FIN RAW LAYER ===

    spark.stop()
    duration = round(time.time() - start, 1)
    logger.info(f"[SPARK] Terminé | durée: {duration}s")


if __name__ == "__main__":
    run()
