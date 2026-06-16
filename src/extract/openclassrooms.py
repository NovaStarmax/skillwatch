import json
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logger import get_logger

load_dotenv()

URL = "https://openclassrooms.com/fr/paths"
HTML_PATH = ROOT / "data" / "raw" / "scraping" / "openclassrooms.html"
TRAINING_MAPPING_PATH = ROOT / "config" / "training_skills_mapping.json"


def fetch_html(path: Path, logger) -> str:
    if path.exists():
        logger.info("[SCRAPING] HTML déjà présent → parsing direct")
        return path.read_text(encoding="utf-8")

    logger.info("[SCRAPING] HTML absent → lancement Playwright")
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"Accept-Language": "fr-FR,fr;q=0.9"})

            page.goto("https://openclassrooms.com/fr/paths",
                      wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            # Fermer la bannière cookies TrustArc si présente
            try:
                cookie_selectors = [
                    "a:has-text('Refuser tout')",
                    "a:has-text('Tout refuser')",
                    "button:has-text('Refuser')",
                    "#truste-consent-button",
                    ".truste-button2",
                    "[id*='consent'] button",
                ]
                for selector in cookie_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=1000):
                            btn.click()
                            page.wait_for_timeout(1000)
                            logger.info("[SCRAPING] Bannière cookies fermée")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Alternative : forcer la suppression via JavaScript
            page.evaluate("""
                const banner = document.getElementById('consent_blackbar');
                if (banner) banner.remove();
                const overlay = document.getElementById('trustarc-banner-overlay');
                if (overlay) overlay.remove();
            """)
            page.wait_for_timeout(500)

            max_clicks = 15
            clicks = 0

            while clicks < max_clicks:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)

                try:
                    btn = page.locator("span", has_text="Voir plus de parcours").first
                    if btn.is_visible(timeout=2000):
                        btn.scroll_into_view_if_needed()
                        page.wait_for_timeout(500)
                        btn.dispatch_event("click")
                        page.wait_for_timeout(2000)
                        clicks += 1
                        logger.info(f"[SCRAPING] Clic 'Voir plus de parcours' {clicks}")
                    else:
                        logger.info("[SCRAPING] Bouton plus visible → toutes formations chargées")
                        break
                except Exception as e:
                    logger.info(f"[SCRAPING] Fin pagination: {e}")
                    break

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            html_content = page.content()
            browser.close()

    except Exception as e:
        logger.error(f"[SCRAPING] Timeout ou erreur Playwright: {e}")
        sys.exit(1)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")
    logger.info(f"[SCRAPING] HTML sauvegardé ({len(html_content.encode('utf-8'))} bytes)")
    return html_content


def parse_formations(html: str, logger) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    formations = []

    for card in soup.select("a[href*='/fr/paths/']"):
        href = card.get("href", "")
        if not href or href == "/fr/paths":
            continue

        url = f"https://openclassrooms.com{href}" if href.startswith("/") else href

        # Titre
        title_tag = card.select_one("h2, h3, [class*='title'], [class*='Title']")
        title = title_tag.get_text(strip=True) if title_tag else card.get_text(strip=True)[:100]
        if not title:
            continue

        # Domaine
        domain_tag = card.select_one("[class*='domain'], [class*='Domain'], [class*='category'], [class*='tag']")
        domain = domain_tag.get_text(strip=True) if domain_tag else None

        # Niveau / certification
        level_tag = card.select_one("[class*='level'], [class*='Level'], [class*='diploma'], [class*='badge']")
        level = level_tag.get_text(strip=True) if level_tag else None

        # Durée
        card_text = card.get_text(" ", strip=True)
        duration_match = re.search(r"(\d+)\s*mois", card_text)
        duration_months = int(duration_match.group(1)) if duration_match else None

        formations.append({
            "title": title,
            "domain": domain,
            "level": level,
            "duration_months": duration_months,
            "url": url,
            "provider": "OpenClassrooms",
        })

    # Déduplication sur url
    seen_urls: set[str] = set()
    unique = []
    for f in formations:
        if f["url"] not in seen_urls:
            seen_urls.add(f["url"])
            unique.append(f)

    logger.info(f"[SCRAPING] {len(unique)} formations extraites")
    return unique


def match_skills(title: str, mapping: dict[str, list[str]]) -> list[str]:
    return mapping.get(title, [])


def run() -> None:
    logger = get_logger("scraping")

    # Connexion warehouse
    try:
        engine = get_engine()
        engine.connect().close()
    except Exception as e:
        logger.error(f"[SCRAPING] DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    # Chargement du mapping formations → skills
    with open(TRAINING_MAPPING_PATH, encoding="utf-8") as f:
        training_mapping: dict[str, list[str]] = json.load(f)

    html = fetch_html(HTML_PATH, logger)
    formations = parse_formations(html, logger)

    matched_count = 0
    unmatched_count = 0
    training_count = 0
    skill_links = 0
    start = time.time()

    with engine.connect() as conn:
        for formation in formations:
            if not formation.get("url"):
                continue

            # Upsert training
            row = conn.execute(
                text("""
                    INSERT INTO trainings (title, domain, level, duration_months, provider, url)
                    VALUES (:title, :domain, :level, :duration_months, :provider, :url)
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        domain = EXCLUDED.domain
                    RETURNING id
                """),
                {
                    "title": formation["title"],
                    "domain": formation["domain"],
                    "level": formation["level"],
                    "duration_months": formation["duration_months"],
                    "provider": formation["provider"],
                    "url": formation["url"],
                },
            ).fetchone()

            if not row:
                continue
            training_id = row[0]
            training_count += 1

            # Matching skills
            skills = match_skills(formation["title"], training_mapping)
            if not skills:
                logger.warning(f"[SCRAPING] Titre non mappé: {formation['title']}")
                unmatched_count += 1
                continue

            matched_count += 1
            for skill_name in skills:
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
                        INSERT INTO training_skills (training_id, skill_id)
                        VALUES (:training_id, :skill_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"training_id": training_id, "skill_id": skill_row[0]},
                )
                skill_links += 1

        conn.commit()

    duration = round(time.time() - start, 1)
    logger.info(f"[SCRAPING] {matched_count} formations matchées dans training_skills_mapping.json")
    logger.info(f"[SCRAPING] {unmatched_count} formations sans skill détecté")
    logger.info(
        f"[SCRAPING] Upsert terminé | {training_count} trainings | {skill_links} liaisons | durée: {duration}s"
    )


if __name__ == "__main__":
    run()
