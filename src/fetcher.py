import asyncio
from datetime import datetime
from typing import Optional

import feedparser
import httpx
from loguru import logger
from sqlmodel import Session

from src.database import get_active_feeds
from src.models import FeedSource

# ── Costanti ───────────────────────────────────────────────────
TIMEOUT = 15
MAX_CONCURRENT = 10
USER_AGENT = "Mozilla/5.0 (compatible; DritaraBot/1.0; +https://dritara.tech)"


# ── Fetch singolo feed ─────────────────────────────────────────
async def fetch_feed(
    client: httpx.AsyncClient,
    source: FeedSource,
) -> tuple[FeedSource, list[dict], Optional[str]]:
    """
    Fetcha un singolo feed RSS.
    Ritorna (source, articoli_grezzi, errore_o_None).
    """
    try:
        response = await client.get(
            source.url,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        response.raise_for_status()

        parsed = feedparser.parse(response.text)
        articles = []

        for entry in parsed.entries:
            title = _clean(getattr(entry, "title", ""))
            url = _clean(getattr(entry, "link", ""))

            if not title or not url:
                continue

            excerpt = _extract_excerpt(entry)
            published_at = _parse_date(entry)

            articles.append(
                {
                    "feed_source_id": source.id,
                    "feed_name": source.name,
                    "feed_level": source.level,
                    "title": title,
                    "url": url,
                    "excerpt": excerpt,
                    "published_at": published_at,
                }
            )

        logger.debug(f"✓ {source.name}: {len(articles)} articoli")
        return source, articles, None

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:120]}"
        logger.warning(f"✗ {source.name}: {error_msg}")
        return source, [], error_msg


# ── Fetch tutti i feed ─────────────────────────────────────────
async def fetch_all_feeds(
    session: Session,
) -> tuple[list[dict], list[dict]]:
    """
    Fetcha tutti i feed attivi in parallelo.
    Ritorna (articoli_grezzi, feed_errors).

    feed_errors = [{"source_id": int, "name": str, "error": str}]
    """
    sources = get_active_feeds(session)
    logger.info(f"Fetch avviato — {len(sources)} feed attivi")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    all_articles = []
    feed_errors = []

    async def bounded_fetch(client, source):
        async with semaphore:
            return await fetch_feed(client, source)

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        tasks = [bounded_fetch(client, src) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    now = datetime.utcnow()

    for source, articles, error in results:
        # Aggiorna statistiche fonte nel DB
        source.last_fetched_at = now
        if error:
            source.consecutive_errors += 1
            source.notes = f"ERROR: {error[:200]}"
            feed_errors.append(
                {
                    "source_id": source.id,
                    "name": source.name,
                    "error": error,
                }
            )
        else:
            source.last_success_at = now
            source.consecutive_errors = 0
            source.notes = None
            all_articles.extend(articles)

        session.add(source)

    session.commit()

    ok = len(sources) - len(feed_errors)
    total = sum(len(r[1]) for r in results)
    logger.info(
        f"Fetch completato — {ok}/{len(sources)} feed OK — {total} articoli grezzi"
    )

    return all_articles, feed_errors


# ── Helper ─────────────────────────────────────────────────────
def _clean(text: str) -> str:
    return " ".join(text.strip().split())


def _extract_excerpt(entry) -> Optional[str]:
    """Estrae il testo migliore disponibile come excerpt."""
    # Prova summary, poi description, poi content
    for attr in ("summary", "description"):
        text = getattr(entry, attr, "")
        if text:
            return _strip_html(_clean(text))[:500]

    if hasattr(entry, "content") and entry.content:
        text = entry.content[0].get("value", "")
        if text:
            return _strip_html(_clean(text))[:500]

    return None


def _strip_html(text: str) -> str:
    """Rimuove tag HTML basilari dal testo."""
    import re

    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"&[a-zA-Z]+;", " ", clean)
    return " ".join(clean.split())


def _parse_date(entry) -> Optional[datetime]:
    """Estrae la data di pubblicazione dall'entry."""

    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6])
            except Exception:
                pass
    return None
