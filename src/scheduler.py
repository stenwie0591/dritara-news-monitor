"""
Scheduler principale — orchestra fetch, notifica admin e pubblicazione.

Flusso giornaliero:
  07:00 — fetch + score + notifica admin
  09:00 — pubblica articolo approvato (se presente)
  13:00 — pubblica articolo approvato (se presente)
  18:00 — pubblica articolo approvato (se presente)
  22:00 — pubblica articolo approvato (se presente)
"""

from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from src.database import get_session
from src.deduplicator import Deduplicator
from src.fetcher import fetch_all_feeds
from src.models import Article
from src.monitor import send_heartbeat
from src.scorer import build_scorer
from src.sender_telegram import (
    PUBLISH_HOURS,
    get_next_to_publish,
    mark_published,
    mark_publishing,
    notify_admin,
    publish_article,
)


# ── Job: fetch + score + notifica ─────────────────────────────
async def job_fetch_and_notify() -> None:
    logger.info("=== JOB: fetch + score + notifica admin ===")
    today = date.today()
    session = next(get_session())

    try:
        # Fetch
        articles_raw, errors = await fetch_all_feeds(session)
        logger.info(f"Fetch: {len(articles_raw)} grezzi, {len(errors)} errori")

        # Dedup
        dedup = Deduplicator()
        articles_unique = dedup.filter(articles_raw)
        logger.info(f"Dopo dedup: {len(articles_unique)} unici")

        # Score e salva in DB
        scorer = build_scorer(session)
        section1 = []
        saved = 0

        for a in articles_unique:
            scored = scorer.score(
                title=a["title"],
                excerpt=a.get("excerpt", ""),
                feed_level=a.get("feed_level", 2),
            )
            if scored.section != "discarded":
                # Salta se l'articolo è già nel DB
                from src.database import article_exists

                if article_exists(session, a["id"]):
                    continue
                article = Article(
                    id=a["id"],
                    title=a["title"],
                    excerpt=a.get("excerpt", ""),
                    url=a["url"],
                    feed_name=a["feed_name"],
                    feed_source_id=a["feed_source_id"],
                    feed_level=a["feed_level"],
                    published_at=a.get("published_at"),
                    score=scored.score,
                    score_detail=str(scored.score_detail),
                    section=scored.section,
                    keyword_matches=str(scored.keyword_matches),
                    digest_date=today,
                )
                session.add(article)
                saved += 1

                if scored.section == "section1":
                    section1.append(
                        {
                            "id": a["id"],
                            "title": a["title"],
                            "excerpt": a.get("excerpt", ""),
                            "feed_name": a["feed_name"],
                            "url": a["url"],
                            "score": scored.score,
                        }
                    )

        session.commit()
        logger.info(f"Salvati {saved} articoli — Section1: {len(section1)}")

        # Notifica admin con articoli section1 ordinati per score
        section1.sort(key=lambda x: x["score"], reverse=True)
        await notify_admin(section1, today)

        # Alert immediato per feed con errori critici
        from src.sender_telegram import alert_feed_errors

        await alert_feed_errors(errors)

    except Exception as e:
        logger.error(f"Errore job fetch: {e}")
    finally:
        session.close()


# ── Job: pubblicazione oraria ──────────────────────────────────
async def job_publish(hour: int) -> None:
    logger.info(f"=== JOB: pubblicazione ore {hour}:00 ===")

    article = get_next_to_publish(date.today(), hour=hour)
    if not article:
        logger.info(f"Nessun articolo approvato per le {hour}:00")
        return

    mark_publishing(article["queue_id"])
    success = await publish_article(article)
    if success:
        mark_published(article["queue_id"])
        logger.info(f"Pubblicato alle {hour}:00: {article['title'][:60]}")
    else:
        logger.error(f"Errore pubblicazione alle {hour}:00")


# ── Recovery job saltati ───────────────────────────────────────
async def job_startup_recovery() -> None:
    """
    Eseguito all'avvio: se il fetch di oggi non è ancora stato fatto
    (nessun articolo con digest_date = oggi), lo lancia immediatamente.
    """
    session = next(get_session())
    try:
        from sqlmodel import select

        today = date.today()
        existing = session.exec(
            select(Article).where(Article.digest_date == today).limit(1)
        ).first()
        if not existing:
            logger.warning("Recovery: fetch di oggi non trovato — rilancio immediato")
            await job_fetch_and_notify()
        else:
            logger.info("Recovery: fetch di oggi già presente — nessuna azione")
    except Exception as e:
        logger.error(f"Errore recovery startup: {e}")
    finally:
        session.close()


# ── Setup scheduler ────────────────────────────────────────────
def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")

    # Fetch + notifica admin alle 07:00
    scheduler.add_job(
        job_fetch_and_notify,
        CronTrigger(hour=7, minute=0, timezone="Europe/Rome"),
        id="fetch_and_notify",
        name="Fetch + Notifica admin",
        replace_existing=True,
    )

    # Heartbeat alle 7:05
    scheduler.add_job(
        send_heartbeat,
        CronTrigger(hour=7, minute=5, timezone="Europe/Rome"),
        id="heartbeat",
        name="Heartbeat sistema",
        replace_existing=True,
    )

    # Pubblicazione agli orari prestabiliti
    for hour in PUBLISH_HOURS:
        scheduler.add_job(
            job_publish,
            CronTrigger(hour=hour, minute=0, timezone="Europe/Rome"),
            id=f"publish_{hour}",
            name=f"Pubblicazione ore {hour}:00",
            args=[hour],
            replace_existing=True,
        )

        # Recovery all'avvio — lancia fetch se oggi non è ancora stato fatto
    scheduler.add_job(
        job_startup_recovery,
        "date",  # eseguito una sola volta, subito
        id="startup_recovery",
        name="Recovery job saltati",
        replace_existing=True,
    )

    return scheduler
