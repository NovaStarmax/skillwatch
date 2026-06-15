import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_demographics_engine, get_engine
from src.utils.logger import get_logger

load_dotenv()

AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
KEYWORDS = ["data engineer", "data scientist", "développeur python", "machine learning"]
SKILLS_MAPPING_PATH = ROOT / "config" / "skills_mapping.json"
UNMATCHED_LOG = ROOT / "data" / "unmatched.log"

_token: str | None = None
_expires_at: float = 0.0


def authenticate(logger) -> None:
    global _token, _expires_at
    resp = requests.post(
        f"{AUTH_URL}?realm=/partenaire",
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("FRANCE_TRAVAIL_CLIENT_ID"),
            "client_secret": os.getenv("FRANCE_TRAVAIL_CLIENT_SECRET"),
            "scope": "api_offresdemploiv2 o2dsoffre",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    resp.raise_for_status()
    _token = resp.json()["access_token"]
    _expires_at = time.time() + 1499
    logger.info("[FRANCE TRAVAIL] Authentification OK | token valide 1499s")


def refresh_token_if_needed(logger) -> None:
    if time.time() > _expires_at - 30:
        authenticate(logger)


def fetch_offers(keyword: str, logger) -> list[dict]:
    for attempt in range(2):
        refresh_token_if_needed(logger)
        try:
            resp = requests.get(
                SEARCH_URL,
                params={"motsCles": keyword, "range": "0-149"},
                headers={"Authorization": f"Bearer {_token}"},
                timeout=15,
            )
            if resp.status_code == 401:
                if attempt == 0:
                    authenticate(logger)
                    continue
                logger.error("[FRANCE TRAVAIL] Token invalide après refresh → exit")
                sys.exit(1)
            if resp.status_code == 429:
                if attempt == 0:
                    time.sleep(2)
                    continue
                logger.warning(
                    f'[FRANCE TRAVAIL] Rate limit persistant sur "{keyword}" → skip'
                )
                return []
            resp.raise_for_status()
            results = resp.json().get("resultats", [])
            logger.info(
                f'[FRANCE TRAVAIL] Requête: "{keyword}" | {len(results)} offres récupérées'
            )
            return results
        except requests.Timeout:
            logger.warning(f'[FRANCE TRAVAIL] Timeout sur "{keyword}" → skip')
            return []
        except requests.RequestException as e:
            logger.warning(f'[FRANCE TRAVAIL] Erreur sur "{keyword}": {e} → skip')
            return []
    return []


def parse_salary(libelle: str | None) -> tuple[int | None, int | None]:
    if not libelle:
        return None, None
    match = re.search(r"(\d+(?:\.\d+)?)\s*Euros?\s*à\s*(\d+(?:\.\d+)?)", libelle)
    if match:
        return int(float(match.group(1))), int(float(match.group(2)))
    return None, None


def get_dept_population(dept_code: str, demo_conn) -> int | None:
    try:
        row = demo_conn.execute(
            text("SELECT population FROM departments WHERE dep = :dep"),
            {"dep": dept_code},
        ).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def upsert_skill(canonical: str, conn) -> int | None:
    conn.execute(
        text("""
            INSERT INTO skills (name, category)
            VALUES (:name, 'unknown')
            ON CONFLICT (name) DO NOTHING
        """),
        {"name": canonical},
    )
    row = conn.execute(
        text("SELECT id FROM skills WHERE name = :name"),
        {"name": canonical},
    ).fetchone()
    return row[0] if row else None


def run() -> None:
    logger = get_logger("france_travail")

    # Connexion warehouse (obligatoire)
    try:
        warehouse_engine = get_engine()
        warehouse_engine.connect().close()
    except Exception as e:
        logger.error(f"[FRANCE TRAVAIL] DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    # Connexion demographics (optionnelle)
    demo_engine = None
    try:
        demo_engine = get_demographics_engine()
        demo_engine.connect().close()
    except Exception as e:
        logger.warning(
            f"[FRANCE TRAVAIL] DEMOGRAPHICS_URL inaccessible: {e} → enrichissement désactivé"
        )

    # Auth
    authenticate(logger)

    # Collecte
    raw_offers: list[dict] = []
    for keyword in KEYWORDS:
        raw_offers.extend(fetch_offers(keyword, logger))
        time.sleep(0.5)

    # Déduplication en mémoire
    seen: set[str] = set()
    unique_offers: list[dict] = []
    for offer in raw_offers:
        ext_id = offer.get("id")
        if ext_id and ext_id not in seen:
            seen.add(ext_id)
            unique_offers.append(offer)
    logger.info(
        f"[FRANCE TRAVAIL] Total brut: {len(raw_offers)} | {len(unique_offers)} uniques après déduplication"
    )

    # Chargement du mapping skills
    with open(SKILLS_MAPPING_PATH, encoding="utf-8") as f:
        mapping: dict[str, str] = json.load(f)

    UNMATCHED_LOG.parent.mkdir(parents=True, exist_ok=True)

    enriched_count = 0
    skills_matched = 0
    unmatched_count = 0
    start = time.time()

    with warehouse_engine.connect() as wconn:
        demo_conn = demo_engine.connect() if demo_engine else None

        for offer in unique_offers:
            external_id = offer.get("id")
            title = offer.get("intitule", "") or ""
            description = offer.get("description", "") or ""
            company = offer.get("entreprise", {}).get("nom")
            lieu = offer.get("lieuTravail", {})
            location = lieu.get("libelle")
            commune = lieu.get("commune") or ""
            dept_code = commune[:2] if commune else None
            contract_type = offer.get("typeContrat")
            published_at = offer.get("dateCreation")

            # Enrichissement démographique
            dept_population = None
            if demo_conn and dept_code:
                dept_population = get_dept_population(dept_code, demo_conn)
                if dept_population is not None:
                    enriched_count += 1

            # Parsing salaire
            salary_libelle = (offer.get("salaire") or {}).get("libelle")
            salary_min, salary_max = parse_salary(salary_libelle)

            # Upsert job_offer
            row = wconn.execute(
                text("""
                    INSERT INTO job_offers (
                        external_id, title, company, location,
                        dept_code, dept_population,
                        salary_min, salary_max,
                        contract_type, source, published_at
                    ) VALUES (
                        :external_id, :title, :company, :location,
                        :dept_code, :dept_population,
                        :salary_min, :salary_max,
                        :contract_type, 'france_travail', :published_at
                    )
                    ON CONFLICT (external_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        dept_population = EXCLUDED.dept_population,
                        salary_min = EXCLUDED.salary_min,
                        salary_max = EXCLUDED.salary_max
                    RETURNING id
                """),
                {
                    "external_id": external_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "dept_code": dept_code,
                    "dept_population": dept_population,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "contract_type": contract_type,
                    "published_at": published_at,
                },
            ).fetchone()
            job_offer_id = row[0]

            # Matching skills
            offer_text = f"{title} {description}".lower()
            matched: list[str] = []
            for alias, canonical in mapping.items():
                if alias in offer_text and canonical not in matched:
                    matched.append(canonical)

            if matched:
                for canonical in matched:
                    skill_id = upsert_skill(canonical, wconn)
                    if skill_id:
                        wconn.execute(
                            text("""
                                INSERT INTO job_offer_skills (job_offer_id, skill_id)
                                VALUES (:job_offer_id, :skill_id)
                                ON CONFLICT DO NOTHING
                            """),
                            {"job_offer_id": job_offer_id, "skill_id": skill_id},
                        )
                        skills_matched += 1
            else:
                unmatched_count += 1
                with open(UNMATCHED_LOG, "a", encoding="utf-8") as f:
                    f.write(
                        f"[UNMATCHED] source: france_travail | offre: {external_id} | title: {title}\n"
                    )

        wconn.commit()
        if demo_conn:
            demo_conn.close()

    duration = round(time.time() - start, 1)
    logger.info(
        f"[FRANCE TRAVAIL] Enrichissement démographique: {enriched_count}/{len(unique_offers)} offres enrichies"
    )
    logger.info(
        f"[FRANCE TRAVAIL] Skills matchés: {skills_matched} liaisons | {unmatched_count} non-matchés → data/unmatched.log"
    )
    logger.info(f"[FRANCE TRAVAIL] Upsert terminé | durée: {duration}s")


if __name__ == "__main__":
    run()
