import argparse
import time

from dotenv import load_dotenv

from src.extract.demographics import run as run_demographics
from src.extract.france_travail import run as run_france_travail
from src.extract.stackoverflow_latest import run as run_stackoverflow
from src.extract.stackoverflow_spark import run as run_spark
from src.extract.openclassrooms import run as run_openclassrooms
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger("pipeline")

STEPS = ["extract", "transform", "load", "all"]
SOURCES = ["france_travail", "stackoverflow", "openclassrooms", "spark", "demographics", "all"]

EXTRACT_RUNNERS = [
    ("demographics", run_demographics),
    ("france_travail", run_france_travail),
    ("stackoverflow", run_stackoverflow),
    ("spark", run_spark),
    ("openclassrooms", run_openclassrooms),
]

SOURCE_MAP = {name: fn for name, fn in EXTRACT_RUNNERS}


def run_transform() -> None:
    from src.transform.normalizer import run as run_normalizer
    run_normalizer()


def _run_extractor(name: str, fn, dry_run: bool) -> None:
    logger.info(f"[PIPELINE] Démarrage | step=extract | source={name}")
    if dry_run:
        logger.info(f"[PIPELINE] dry-run | source={name} | durée=0.0s")
        return
    start = time.time()
    fn()
    duration = round(time.time() - start, 1)
    logger.info(f"[PIPELINE] Terminé | source={name} | durée={duration}s")


def run_step(step: str, source: str, dry_run: bool) -> None:
    if step == "all":
        for name, fn in EXTRACT_RUNNERS:
            _run_extractor(name, fn, dry_run)
        logger.info("[PIPELINE] Démarrage | step=transform")
        if not dry_run:
            run_transform()
        else:
            logger.info("[PIPELINE] dry-run | step=transform | durée=0.0s")
        return

    if step == "extract":
        if source == "all":
            for name, fn in EXTRACT_RUNNERS:
                _run_extractor(name, fn, dry_run)
        else:
            _run_extractor(source, SOURCE_MAP[source], dry_run)
        return

    if step == "transform":
        logger.info("[PIPELINE] Démarrage | step=transform")
        if not dry_run:
            run_transform()
        else:
            logger.info("[PIPELINE] dry-run | step=transform | durée=0.0s")
        return

    logger.info(f"[PIPELINE] step={step} | Not implemented yet")


def main() -> None:
    parser = argparse.ArgumentParser(description="SkillWatch pipeline CLI")
    parser.add_argument(
        "--step",
        choices=STEPS,
        default="all",
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--source",
        choices=SOURCES,
        default="all",
        help="Data source to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without executing any action",
    )

    args = parser.parse_args()
    run_step(args.step, args.source, args.dry_run)


if __name__ == "__main__":
    main()
