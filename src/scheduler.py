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
from src.drive import upload_csv_giornaliero, upload_sqlite_backup
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


def _promote_fallback_section1(articles: list, max_promote: int = 2) -> None:
    """
    Se section1 è vuota, promuove i migliori articoli section2.
    Priorità: territorial_boost=True, poi score puro.
    Massimo max_promote articoli promossi.
    """
    s2 = [a for a in articles if a.section == "section2"]
    if not s2:
        return

    import ast

    with_boost = []
    for a in s2:
        try:
            detail = (
                ast.literal_eval(a.score_detail)
                if isinstance(a.score_detail, str)
                else a.score_detail
            )
            if detail.get("territorial_boost"):
                with_boost.append(a)
        except Exception:
            pass

    candidates = sorted(with_boost, key=lambda x: x.score, reverse=True)

    if not candidates:
        candidates = sorted(s2, key=lambda x: x.score, reverse=True)

    for a in candidates[:max_promote]:
        a.section = "section1"
        logger.info(f"Fallback section1 promosso: {a.title[:60]} (score {a.score})")


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

        # Salva statistiche per feed
        from sqlmodel import select as sql_select

        from src.models import FeedStats

        feed_fetched: dict = {}
        feed_relevant: dict = {}

        for a in articles_unique:
            fid = a["feed_source_id"]
            fname = a["feed_name"]
            feed_fetched[fid] = (fname, feed_fetched.get(fid, (fname, 0))[1] + 1)

        for a in articles_unique:
            scored = scorer.score(
                title=a["title"],
                excerpt=a.get("excerpt", ""),
                feed_level=a.get("feed_level", 2),
            )
            if scored.section != "discarded":
                fid = a["feed_source_id"]
                fname = a["feed_name"]
                feed_relevant[fid] = (fname, feed_relevant.get(fid, (fname, 0))[1] + 1)

        for fid, (fname, n_fetched) in feed_fetched.items():
            _, n_relevant = feed_relevant.get(fid, (fname, 0))
            existing_stat = session.exec(
                sql_select(FeedStats)
                .where(FeedStats.feed_source_id == fid)
                .where(FeedStats.fetch_date == today)
            ).first()
            if existing_stat:
                existing_stat.articles_fetched = n_fetched
                existing_stat.articles_relevant = n_relevant
                session.add(existing_stat)
            else:
                session.add(
                    FeedStats(
                        feed_source_id=fid,
                        feed_name=fname,
                        fetch_date=today,
                        articles_fetched=n_fetched,
                        articles_relevant=n_relevant,
                    )
                )

        session.commit()

        # Carica tutti gli articoli di oggi
        # (serve sia per fallback section1 che per costruire section2)
        all_today = session.exec(
            sql_select(Article).where(Article.digest_date == today)
        ).all()

        # Fallback section1: se vuota, promuovi i migliori da section2
        if not section1:
            _promote_fallback_section1(all_today)
            session.commit()
            for a in all_today:
                if a.section == "section1":
                    section1.append(
                        {
                            "id": a.id,
                            "title": a.title,
                            "excerpt": a.excerpt,
                            "feed_name": a.feed_name,
                            "url": a.url,
                            "score": a.score,
                        }
                    )
            if section1:
                logger.info(
                    f"Fallback attivato — {len(section1)} articoli promossi a section1"
                )

        logger.info(f"FeedStats salvate per {len(feed_fetched)} feed")
        logger.info(f"Salvati {saved} articoli — Section1: {len(section1)}")

        # Costruisci lista section2 top 5 per score
        section2 = sorted(
            [
                {
                    "id": a.id,
                    "title": a.title,
                    "excerpt": a.excerpt,
                    "feed_name": a.feed_name,
                    "url": a.url,
                    "score": a.score,
                }
                for a in all_today
                if a.section == "section2"
            ],
            key=lambda x: x["score"],
            reverse=True,
        )[:5]

        # Notifica admin con section1 + section2
        section1.sort(key=lambda x: x["score"], reverse=True)
        await notify_admin(section1, today, articles_s2=section2)

        # Upload CSV giornaliero su Drive
        from sqlmodel import select as sql_select_pq

        from src.models import PublishQueue

        all_relevant = session.exec(
            sql_select_pq(Article).where(Article.digest_date == today)
        ).all()

        queue_today = session.exec(
            sql_select_pq(PublishQueue).where(PublishQueue.digest_date == today)
        ).all()
        queue_status = {q.article_id: q.status for q in queue_today}

        articles_for_csv = [
            {
                "title": a.title,
                "url": a.url,
                "feed_name": a.feed_name,
                "section": a.section,
                "score": round(a.score, 2),
                "keyword_matches": a.get_keyword_matches(),
                "status": queue_status.get(a.id, "pending"),
            }
            for a in all_relevant
        ]

        upload_csv_giornaliero(articles_for_csv, today)

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


# ── Recovery stati orfani ──────────────────────────────────────
async def job_recover_orphan_publishing() -> None:
    """
    Eseguito all'avvio: riporta a 'approved' qualsiasi articolo
    rimasto bloccato in stato 'publishing' a causa di un crash.
    """
    from sqlmodel import select

    from src.models import PublishQueue

    session = next(get_session())
    try:
        orfani = session.exec(
            select(PublishQueue).where(PublishQueue.status == "publishing")
        ).all()

        if not orfani:
            logger.info("Recovery publishing: nessun articolo orfano trovato")
            return

        for q in orfani:
            q.status = "approved"
            session.add(q)
            logger.warning(
                f"Recovery publishing: articolo {q.article_id[:16]}... "
                f"riportato da 'publishing' a 'approved'"
            )

        session.commit()
        logger.info(f"Recovery publishing: {len(orfani)} articoli ripristinati")

        import os

        from src.sender_telegram import _send

        admin_id = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))
        if admin_id:
            await _send(
                admin_id,
                (
                    f"⚠️ *Recovery al riavvio*\n\n"
                    f"{len(orfani)} articolo/i era bloccato in stato `publishing` "
                    f"(probabile crash precedente).\n"
                    f"Riportato/i ad `approved` — verrà pubblicato al prossimo slot orario."
                ),
            )

    except Exception as e:
        logger.error(f"Errore recovery publishing orfano: {e}")
    finally:
        session.close()


# ── Recovery job saltati ───────────────────────────────────────
async def job_startup_recovery() -> None:
    """
    Eseguito all'avvio: se il fetch di oggi non è ancora stato fatto
    (nessun articolo con digest_date = oggi), lo lancia immediatamente.
    Esegue anche il recovery degli stati publishing orfani.
    """
    await job_recover_orphan_publishing()

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


# ── Job: pulizia DB settimanale ────────────────────────────────
async def job_cleanup_db() -> None:
    """
    Eseguito ogni domenica notte alle 02:00.
    Cancella articoli e relative voci in coda più vecchi di 90 giorni.
    """
    from datetime import timedelta

    from sqlmodel import select

    from src.models import PublishQueue

    session = next(get_session())
    try:
        cutoff = date.today() - timedelta(days=90)
        logger.info(f"Pulizia DB: rimozione articoli antecedenti al {cutoff}")

        old_queue = session.exec(
            select(PublishQueue).where(PublishQueue.digest_date < cutoff)
        ).all()
        for q in old_queue:
            session.delete(q)

        old_articles = session.exec(
            select(Article).where(Article.digest_date < cutoff)
        ).all()
        n_articles = len(old_articles)
        for a in old_articles:
            session.delete(a)

        session.commit()
        logger.info(f"Pulizia DB completata: {n_articles} articoli rimossi")

    except Exception as e:
        logger.error(f"Errore pulizia DB: {e}")
    finally:
        session.close()


# ── Job: backup SQLite su Drive ────────────────────────────────
async def job_backup_drive() -> None:
    """Backup SQLite su Drive — eseguito ogni domenica alle 02:30."""
    from pathlib import Path

    logger.info("=== JOB: backup SQLite su Drive ===")
    db_path = Path("data/dritara.db")
    file_id = upload_sqlite_backup(db_path, date.today())
    if file_id:
        logger.info(f"Backup Drive completato: {file_id}")
    else:
        logger.error("Backup Drive fallito")


# ── Setup scheduler ────────────────────────────────────────────
def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Rome")

    scheduler.add_job(
        job_fetch_and_notify,
        CronTrigger(hour=7, minute=0, timezone="Europe/Rome"),
        id="fetch_and_notify",
        name="Fetch + Notifica admin",
        replace_existing=True,
    )

    scheduler.add_job(
        send_heartbeat,
        CronTrigger(hour=7, minute=5, timezone="Europe/Rome"),
        id="heartbeat",
        name="Heartbeat sistema",
        replace_existing=True,
    )

    scheduler.add_job(
        job_cleanup_db,
        CronTrigger(day_of_week="sun", hour=2, minute=0, timezone="Europe/Rome"),
        id="cleanup_db",
        name="Pulizia DB settimanale",
        replace_existing=True,
    )

    scheduler.add_job(
        job_backup_drive,
        CronTrigger(day_of_week="sun", hour=2, minute=30, timezone="Europe/Rome"),
        id="backup_drive",
        name="Backup SQLite su Drive",
        replace_existing=True,
    )

    for hour in PUBLISH_HOURS:
        scheduler.add_job(
            job_publish,
            CronTrigger(hour=hour, minute=0, timezone="Europe/Rome"),
            id=f"publish_{hour}",
            name=f"Pubblicazione ore {hour}:00",
            args=[hour],
            replace_existing=True,
        )

    scheduler.add_job(
        job_startup_recovery,
        "date",
        id="startup_recovery",
        name="Recovery job saltati",
        replace_existing=True,
    )

    return scheduler
