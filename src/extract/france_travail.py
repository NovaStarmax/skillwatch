import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_warehouse_engine, replace_raw_table
from src.utils.logger import get_logger

load_dotenv()

AUTH_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
KEYWORDS = ["data engineer", "data scientist", "développeur python", "machine learning"]
RAW_TABLE = "raw_france_travail"

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


def run() -> None:
    logger = get_logger("france_travail")

    # Connexion warehouse (raw layer, obligatoire)
    try:
        warehouse_engine = get_warehouse_engine()
        warehouse_engine.connect().close()
    except Exception as e:
        logger.error(f"[FRANCE TRAVAIL] WAREHOUSE_DATABASE_URL inaccessible: {e}")
        sys.exit(1)

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

    # === RAW LAYER : écriture brute, sans parsing salaire ni matching skills ===
    # Écrit dans skillwatch_warehouse (WAREHOUSE_DATABASE_URL).
    raw_rows = []
    for offer in unique_offers:
        lieu = offer.get("lieuTravail") or {}
        raw_rows.append({
            "external_id": offer.get("id"),
            "title": offer.get("intitule", "") or "",
            "description": offer.get("description", "") or "",
            "company": (offer.get("entreprise") or {}).get("nom"),
            "location": lieu.get("libelle"),
            "commune": lieu.get("commune") or "",
            "contract_type": offer.get("typeContrat"),
            "published_at": offer.get("dateCreation"),
            "salaire_libelle": (offer.get("salaire") or {}).get("libelle"),
        })

    df_raw = pd.DataFrame(raw_rows, columns=[
        "external_id", "title", "description", "company", "location",
        "commune", "contract_type", "published_at", "salaire_libelle",
    ])
    df_raw["loaded_at"] = datetime.now(timezone.utc)
    replace_raw_table(warehouse_engine, RAW_TABLE, df_raw)
    logger.info(f"[FRANCE TRAVAIL] {len(df_raw)} lignes chargées dans {RAW_TABLE} (raw, skillwatch_warehouse)")
    # === FIN RAW LAYER ===


if __name__ == "__main__":
    run()
