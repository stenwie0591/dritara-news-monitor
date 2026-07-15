"""
monitor.py — Heartbeat e alert feed in errore.
"""

from datetime import date, datetime, timedelta

from loguru import logger
from sqlmodel import select

from src.config import RuntimeSettings, get_settings
from src.database import get_session
from src.models import Article, FeedSource, FeedStats
from src.sender_telegram import _send as _telegram_send
from src.telegram_renderer import HtmlFragment, TelegramMessage, telegram_renderer

# Feed con 0 articoli rilevanti per N giorni consecutivi → alert
LOW_YIELD_DAYS = 3


async def _send(
    text: str | TelegramMessage, *, settings: RuntimeSettings | None = None
) -> None:
    runtime = (settings or get_settings()).validated_for_runtime()
    await _telegram_send(
        runtime.telegram_admin_chat_id or 0, text, settings=runtime
    )


async def send_heartbeat(*, settings: RuntimeSettings | None = None) -> None:
    runtime = (settings or get_settings()).validated_for_runtime()
    today = date.today()
    session = next(get_session())

    try:
        all_feeds = session.exec(
            select(FeedSource).where(FeedSource.active == True)
        ).all()
        feeds_error = [f for f in all_feeds if (f.consecutive_errors or 0) > 0]
        total = len(all_feeds)
        ok = total - len(feeds_error)
        ko = len(feeds_error)

        articles_today = session.exec(
            select(Article).where(Article.digest_date == today)
        ).all()
        s1 = sum(1 for a in articles_today if a.section == "section1")
        s2 = sum(1 for a in articles_today if a.section == "section2")
        s3 = sum(1 for a in articles_today if a.section == "section3")

        # Feed a bassa resa: 0 articoli rilevanti per LOW_YIELD_DAYS giorni consecutivi
        low_yield_feeds = _get_low_yield_feeds(session, today)

        lines: list[HtmlFragment] = []

        if ko == 0:
            lines.append(
                telegram_renderer.join(
                    "🟢 ", telegram_renderer.bold("Sistema OK"), f" — {ok}/{total} feed attivi"
                )
            )
        else:
            lines.append(
                telegram_renderer.join(
                    "🟡 ",
                    telegram_renderer.bold("Sistema parziale"),
                    f" — {ok}/{total} feed attivi, {ko} in errore",
                )
            )

        if s1 + s2 + s3 == 0:
            lines.append("📭 Nessun articolo rilevante oggi")
        else:
            lines.append(telegram_renderer.text(f"📥 {s1 + s2 + s3} articoli rilevanti raccolti\n"))
            lines.append(telegram_renderer.text(f"🔴 Sezione 1 (Sud + Tech): {s1} articoli"))
            lines.append(telegram_renderer.text(f"🟡 Sezione 2 (Trend naz.): {s2} articoli"))
            lines.append(telegram_renderer.text(f"📋 Sezione 3 (In breve):   {s3} articoli"))

        if feeds_error:
            lines.append(
                telegram_renderer.join(
                    "\n⚠️ ", telegram_renderer.bold(f"Feed in errore ({ko}):")
                )
            )
            for f in feeds_error:
                consecutive = f.consecutive_errors or 0
                error_msg = _get_last_error(f)
                lines.append(
                    telegram_renderer.join(
                        "• ",
                        telegram_renderer.bold(f.name, limit=200),
                        f" ({consecutive} err consecutivi)",
                    )
                )
                lines.append(
                    telegram_renderer.join("  ", telegram_renderer.code(error_msg, limit=200))
                )

        if low_yield_feeds:
            lines.append(
                telegram_renderer.join(
                    "\n📉 ",
                    telegram_renderer.bold(
                        f"Feed a bassa resa (0 articoli rilevanti per {LOW_YIELD_DAYS}+ giorni):"
                    ),
                )
            )
            for fname, n_days, avg_fetched in low_yield_feeds:
                lines.append(
                    telegram_renderer.join(
                        "• ",
                        telegram_renderer.bold(fname, limit=200),
                        f" — {n_days} giorni senza rilevanti "
                        f"(media {avg_fetched:.0f} articoli/giorno fetchati)",
                    )
                )

        lines.append(
            telegram_renderer.join(
                "\n",
                telegram_renderer.italic(
                    f"📅 {today.strftime('%d/%m/%Y')} — {datetime.now().strftime('%H:%M')}"
                ),
            )
        )

        for message in telegram_renderer.split_lines(lines):
            await _send(message, settings=runtime)
        logger.info(
            f"Heartbeat inviato — {ok}/{total} feed OK, "
            f"{s1 + s2 + s3} articoli, {len(low_yield_feeds)} feed a bassa resa"
        )

    except Exception as e:
        logger.error(f"Errore heartbeat: {e}")
        await _send(
            telegram_renderer.message(
                "❌ ",
                telegram_renderer.bold("Errore heartbeat"),
                "\n",
                telegram_renderer.code(e, limit=500),
            ),
            settings=runtime,
        )
    finally:
        session.close()


def _get_low_yield_feeds(session, today: date) -> list[tuple]:
    """
    Restituisce i feed che hanno avuto 0 articoli rilevanti
    per LOW_YIELD_DAYS giorni consecutivi.
    Ritorna lista di (feed_name, n_days_zero, avg_fetched).
    """
    cutoff = today - timedelta(days=LOW_YIELD_DAYS)

    # Recupera stats degli ultimi LOW_YIELD_DAYS giorni
    stats = session.exec(
        select(FeedStats)
        .where(FeedStats.fetch_date >= cutoff)
        .where(FeedStats.fetch_date <= today)
    ).all()

    if not stats:
        return []

    # Raggruppa per feed
    from collections import defaultdict

    feed_stats: dict = defaultdict(list)
    for s in stats:
        feed_stats[s.feed_name].append(s)

    low_yield = []
    for fname, records in feed_stats.items():
        # Considera solo feed con almeno LOW_YIELD_DAYS record
        if len(records) < LOW_YIELD_DAYS:
            continue
        # Tutti i giorni devono avere 0 rilevanti
        if all(r.articles_relevant == 0 for r in records):
            avg_fetched = sum(r.articles_fetched for r in records) / len(records)
            low_yield.append((fname, len(records), avg_fetched))

    low_yield.sort(key=lambda x: x[1], reverse=True)
    return low_yield


def _get_last_error(feed: FeedSource) -> str:
    if feed.notes and feed.notes.startswith("ERROR:"):
        return feed.notes[7:127]
    if feed.last_fetched_at and feed.last_success_at:
        delta = feed.last_fetched_at - feed.last_success_at
        hours = int(delta.total_seconds() / 3600)
        return f"Nessun fetch OK da {hours}h"
    return "Errore sconosciuto — controlla i log"
