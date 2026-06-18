import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count, explode, lit, lower, split, trim
from pyspark.sql.types import StringType
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logger import get_logger

load_dotenv()

ARCHIVE_DIR = ROOT / "data" / "raw" / "stackoverflow_archive"
SKILLS_MAPPING_PATH = ROOT / "config" / "skills_mapping.json"
UNMATCHED_LOG = ROOT / "data" / "logs" / "unmatched_spark.log"

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

    # Connexion warehouse
    try:
        engine = get_engine()
        engine.connect().close()
    except Exception as e:
        logger.error(f"[SPARK] DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    # Vérification dossier archive
    csv_files = sorted(ARCHIVE_DIR.glob("*.csv"))
    if not csv_files:
        logger.error(f"[SPARK] Aucun fichier CSV dans {ARCHIVE_DIR}")
        sys.exit(1)

    # Chargement du mapping skills en mémoire Python
    with open(SKILLS_MAPPING_PATH, encoding="utf-8") as f:
        mapping: dict[str, str] = json.load(f)

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

    # UDF de matching — la closure capture `mapping` du scope Python local
    def match_skill(raw_value: str | None) -> str | None:
        if not raw_value:
            return None
        tokens = {t.strip().lower() for t in raw_value.split(";") if t.strip()}
        for alias, canonical in mapping.items():
            if alias in tokens:
                return canonical
        return None

    from pyspark.sql.functions import udf
    match_skill_udf = udf(match_skill, StringType())

    start = time.time()
    skill_frames = []
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

        n_rows = df.count()
        total_respondents += n_rows
        years_loaded.append(year)
        logger.info(
            f"[SPARK] Fichier: {csv_path.name} | {n_rows} lignes | {useful_col_count} colonnes utiles"
        )

        # Salary cast
        salary_expr = (
            col(SALARY_COL).cast("double")
            if SALARY_COL in available_cols
            else lit(None).cast("double")
        )

        # Une ligne longue par colonne skill disponible
        for skill_col in skill_cols_found:
            partial = df.select(
                col("survey_year"),
                col(skill_col).alias("raw_skills"),
                salary_expr.alias("salary"),
            )
            skill_frames.append(partial)

        # Log colonnes optionnelles absentes
        for opt in OPTIONAL_COLS:
            if opt not in available_cols:
                logger.warning(f"[SPARK] Colonne absente dans {csv_path.name}: {opt} → skip colonne")

    logger.info(
        f"[SPARK] Total: {total_respondents} répondants sur {len(years_loaded)} années"
    )

    if not skill_frames:
        logger.error("[SPARK] Aucune donnée exploitable après lecture des fichiers")
        spark.stop()
        sys.exit(1)

    # Union de tous les DataFrames partiels
    combined = skill_frames[0]
    for frame in skill_frames[1:]:
        combined = combined.union(frame)

    # Explosion + normalisation + matching UDF
    logger.info("[SPARK] Agrégation en cours...")
    exploded = (
        combined
        .filter(col("raw_skills").isNotNull())
        .withColumn("raw_skill", explode(split(col("raw_skills"), ";")))
        .withColumn("raw_skill", lower(trim(col("raw_skill"))))
        .withColumn("canonical_skill", match_skill_udf(col("raw_skill")))
    )

    # Logging des valeurs non matchées
    unmatched_rows = (
        exploded
        .filter(col("canonical_skill").isNull())
        .select("survey_year", "raw_skill")
        .distinct()
        .collect()
    )
    if unmatched_rows:
        UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(UNMATCHED_LOG, "a", encoding="utf-8") as f:
            for row in unmatched_rows:
                f.write(
                    f"[UNMATCHED] source: spark | year: {row['survey_year']} | value: {row['raw_skill']}\n"
                )
        logger.info(f"[SPARK] {len(unmatched_rows)} valeurs non matchées → {UNMATCHED_LOG.name}")

    exploded = exploded.filter(col("canonical_skill").isNotNull())

    # Agrégation par skill et par année
    aggregated = (
        exploded
        .groupBy("canonical_skill", "survey_year")
        .agg(
            count("*").alias("usage_count"),
            avg("salary").alias("avg_salary_usd"),
        )
    )

    results = aggregated.collect()
    logger.info(f"[SPARK] {len(results)} skill-année combinaisons détectées")

    # Upsert PostgreSQL
    logger.info("[SPARK] Upsert PostgreSQL en cours...")
    with engine.connect() as conn:
        for row in results:
            skill_name = row["canonical_skill"]
            year = row["survey_year"]
            usage_count = int(row["usage_count"])
            avg_salary = float(row["avg_salary_usd"]) if row["avg_salary_usd"] is not None else None

            conn.execute(
                text("""
                    INSERT INTO skills (name, category)
                    VALUES (:name, 'unknown')
                    ON CONFLICT (name) DO NOTHING
                """),
                {"name": skill_name},
            )
            skill_row = conn.execute(
                text("SELECT id FROM skills WHERE name = :name"),
                {"name": skill_name},
            ).fetchone()
            if not skill_row:
                continue

            conn.execute(
                text("""
                    INSERT INTO survey_stats (skill_id, year, usage_count, avg_salary_usd)
                    VALUES (:skill_id, :year, :usage_count, :avg_salary_usd)
                    ON CONFLICT (skill_id, year) DO UPDATE SET
                        usage_count = EXCLUDED.usage_count,
                        avg_salary_usd = EXCLUDED.avg_salary_usd
                """),
                {
                    "skill_id": skill_row[0],
                    "year": year,
                    "usage_count": usage_count,
                    "avg_salary_usd": avg_salary,
                },
            )

        conn.commit()

    spark.stop()
    duration = round(time.time() - start, 1)
    logger.info(f"[SPARK] Terminé | durée: {duration}s")


if __name__ == "__main__":
    run()
