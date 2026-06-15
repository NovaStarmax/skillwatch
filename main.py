import argparse
import time

from dotenv import load_dotenv

from src.utils.logger import get_logger

load_dotenv()

logger = get_logger("pipeline")

STEPS = ["extract", "transform", "load", "all"]
SOURCES = ["france_travail", "stackoverflow", "openclassrooms", "spark", "all"]


def run_step(step: str, source: str, dry_run: bool) -> None:
    steps = [step] if step != "all" else ["extract", "transform", "load"]
    sources = [source] if source != "all" else ["france_travail", "stackoverflow", "openclassrooms", "spark"]

    for s in steps:
        for src in sources:
            logger.info(f"[PIPELINE] Démarrage | step={s} | source={src}")
            if not dry_run:
                start = time.time()
                duration = round(time.time() - start, 1)
                logger.info(f"[PIPELINE] Not implemented yet | durée={duration}s")
            else:
                logger.info("[PIPELINE] Not implemented yet | durée=0.0s")


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
