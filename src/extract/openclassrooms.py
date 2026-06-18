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
SKILLS_MAPPING_PATH = ROOT / "config" / "skills_mapping.json"
UNMATCHED_LOG = ROOT / "data" / "logs" / "unmatched_openclassrooms.log"

ALLOWED_DOMAINS = {"Data", "Développement", "Systèmes & Réseaux", "Cybersécurité"}

_PREAMBLE_RE = re.compile(
    r'^vous\s+(?:ma[îi]trisere[zs]|d[ée]couvrirez|apprendrez)\s*',
    re.IGNORECASE,
)


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
    skipped = 0

    for card in soup.select("a[href*='/fr/paths/']"):
        href = card.get("href", "")
        if not href or href == "/fr/paths":
            continue

        url = f"https://openclassrooms.com{href}" if href.startswith("/") else href

        # Domaine
        domain_tag = card.select_one("span.MuiTypography-overline")
        domain = domain_tag.get_text(strip=True) if domain_tag else None

        # Titre
        title_tag = card.select_one("h3.MuiTypography-h6")
        title = title_tag.get_text(strip=True) if title_tag else None
        if not title:
            continue

        # Filtre domaine
        if domain not in ALLOWED_DOMAINS:
            logger.warning(f"[SCRAPING] Domaine ignoré: {domain} | formation: {title}")
            skipped += 1
            continue

        # Niveau
        school_icon = card.find(attrs={"data-testid": "SchoolIcon"})
        level_span = school_icon.find_next("span", class_="MuiTypography-bodySmall") if school_icon else None
        level = level_span.get_text(strip=True).replace('\xa0', ' ') if level_span else None

        # Durée (temps plein, premier TodayIcon)
        today_icon = card.find(attrs={"data-testid": "TodayIcon"})
        dur_span = today_icon.find_next("span", class_="MuiTypography-bodySmall") if today_icon else None
        dur_text = dur_span.get_text(strip=True) if dur_span else ""
        duration_match = re.search(r"(\d+)\s*mois", dur_text)
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

    total = len(unique) + skipped
    logger.info(f"[SCRAPING] {len(unique)} formations retenues sur {total} total après filtre domaine")
    return unique


def fetch_detail_html(url: str, slug: str, logger) -> str:
    detail_path = ROOT / "data" / "raw" / "scraping" / "details" / f"{slug}.html"

    if detail_path.exists():
        logger.info(f"[SCRAPING] Détail déjà présent: {slug} → parsing direct")
        return detail_path.read_text(encoding="utf-8")

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"Accept-Language": "fr-FR,fr;q=0.9"})
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
    except Exception as e:
        logger.error(f"[SCRAPING] Erreur Playwright pour {slug}: {e}")
        return ""

    detail_path.parent.mkdir(parents=True, exist_ok=True)
    detail_path.write_text(html, encoding="utf-8")
    logger.info(f"[SCRAPING] Détail fetché: {slug} ({len(html)} bytes)")
    time.sleep(2)
    return html


def extract_skills_from_detail(
    html: str, slug: str, logger, skills_mapping: dict[str, str]
) -> list[str]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    aside = soup.find("aside", attrs={"data-claire-semantic": "warning"})
    if not aside:
        logger.warning(f"[SCRAPING] Pas de balise aside warning: {slug}")
        return []

    skills_raw = []
    for p in aside.find_all("p"):
        full_text = p.get_text(separator=" ", strip=True)
        strong = p.find("strong")
        if strong:
            strong_text = strong.get_text(strip=True)
            # Cas "Vous maîtriserez ... : SKILL1" → extraire après ":"
            if ":" in strong_text:
                after_colon = strong_text.split(":", 1)[1].strip(" ,")
            # Cas "Vous maîtriserez  SKILL1" (preamble sans ":") → extraire après le verbe
            elif _PREAMBLE_RE.match(strong_text):
                m = _PREAMBLE_RE.match(strong_text)
                after_colon = strong_text[m.end():].strip(" ,")
            else:
                after_colon = ""
            rest = full_text.replace(strong_text, "").strip(" :,")
            skills_text = (after_colon + (", " + rest if rest else "")).strip(", ") if after_colon else rest
        else:
            skills_text = full_text
        if not skills_text:
            continue
        candidates = [s.strip() for s in re.split(r"[,;]", skills_text) if s.strip() and len(s.strip()) > 1]
        if len(candidates) >= 2 or "," in skills_text:
            skills_raw = candidates
            break

    if not skills_raw:
        logger.warning(f"[SCRAPING] Aucune compétence trouvée dans aside: {slug}")
        return []

    matched = []
    unmatched = []
    for raw in skills_raw:
        normalized = raw.strip().lower()
        if normalized in skills_mapping:
            canonical = skills_mapping[normalized]
            if canonical not in matched:
                matched.append(canonical)
        else:
            unmatched.append(raw)

    if unmatched:
        with open(UNMATCHED_LOG, "a", encoding="utf-8") as f:
            for u in unmatched:
                f.write(f"[UNMATCHED] source: openclassrooms_detail | slug: {slug} | value: {u}\n")
        logger.warning(f"[SCRAPING] {len(unmatched)} tags non reconnus pour {slug} → unmatched.log")

    logger.info(f"[SCRAPING] {slug}: {len(matched)} skills extraits ({', '.join(matched[:3])}...)")
    return matched


def run() -> None:
    logger = get_logger("scraping")

    # Connexion warehouse
    try:
        engine = get_engine()
        engine.connect().close()
    except Exception as e:
        logger.error(f"[SCRAPING] DATABASE_URL inaccessible: {e}")
        sys.exit(1)

    # Chargement du mapping skills
    with open(SKILLS_MAPPING_PATH, encoding="utf-8") as f:
        skills_mapping: dict[str, str] = json.load(f)

    html = fetch_html(HTML_PATH, logger)
    formations = parse_formations(html, logger)

    # --- Phase 1 : scraping des pages détail ---
    logger.info(f"[SCRAPING] Début scraping détails | {len(formations)} formations à traiter")
    formation_skills: dict[str, list[str]] = {}
    detail_real = 0

    for formation in formations:
        url = formation["url"]
        slug = url.rstrip("/").split("/")[-1]
        detail_html = fetch_detail_html(url, slug, logger)
        skills = extract_skills_from_detail(detail_html, slug, logger, skills_mapping)
        formation_skills[url] = skills
        if skills:
            detail_real += 1

    logger.info(
        f"[SCRAPING] Détails terminés | {detail_real} formations avec skills réels"
        f" | {len(formations) - detail_real} fallbacks JSON"
    )

    # --- Phase 2 : upsert ---
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
                        domain = EXCLUDED.domain,
                        level = EXCLUDED.level,
                        duration_months = EXCLUDED.duration_months
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

            # Skills : depuis scraping détail uniquement
            skills = formation_skills.get(formation["url"]) or []
            if not skills:
                logger.warning(f"[SCRAPING] Aucun skill trouvé pour: {formation['title']}")
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
    logger.info(f"[SCRAPING] {matched_count} formations avec skills insérés en base")
    logger.info(f"[SCRAPING] {unmatched_count} formations sans skill détecté")
    logger.info(
        f"[SCRAPING] Upsert terminé | {training_count} trainings | {skill_links} liaisons | durée: {duration}s"
    )


if __name__ == "__main__":
    run()
