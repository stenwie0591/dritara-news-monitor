"""
monitor.py — Heartbeat e alert feed in errore.
"""
import os
from datetime import date, datetime

import httpx
from dotenv import load_dotenv
from loguru import logger
from sqlmodel import select

from src.database import get_session
from src.models import Article, FeedSource

load_dotenv()

TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID"))
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


async def _send(text: str) -> None:
    payload = {
        "chat_id": ADMIN_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        data = r.json()
        if not data.get("ok"):
            logger.error(f"Heartbeat send error: {data}")


async def send_heartbeat() -> None:
    today = date.today()
    session = next(get_session())

    try:
        all_feeds   = session.exec(select(FeedSource).where(FeedSource.active == True)).all()
        feeds_error = [f for f in all_feeds if (f.consecutive_errors or 0) > 0]
        total = len(all_feeds)
        ok    = total - len(feeds_error)
        ko    = len(feeds_error)

        articles_today = session.exec(
            select(Article).where(Article.digest_date == today)
        ).all()
        s1 = sum(1 for a in articles_today if a.section == "section1")
        s2 = sum(1 for a in articles_today if a.section == "section2")
        s3 = sum(1 for a in articles_today if a.section == "section3")

        lines = []

        if ko == 0:
            lines.append(f"🟢 *Sistema OK* — {ok}/{total} feed attivi")
        else:
            lines.append(f"🟡 *Sistema parziale* — {ok}/{total} feed attivi, {ko} in errore")

        if s1 + s2 + s3 == 0:
            lines.append("📭 Nessun articolo rilevante oggi")
        else:
            lines.append(f"📥 {s1 + s2 + s3} articoli rilevanti raccolti\n")
            lines.append(f"🔴 Sezione 1 (Sud + Tech): {s1} articoli")
            lines.append(f"🟡 Sezione 2 (Trend naz.): {s2} articoli")
            lines.append(f"📋 Sezione 3 (In breve):   {s3} articoli")

        if feeds_error:
            lines.append(f"\n⚠️ *Feed in errore ({ko}):*")
            for f in feeds_error:
                consecutive = f.consecutive_errors or 0
                error_msg = _get_last_error(f)
                lines.append(f"• *{f.name}* ({consecutive} err consecutivi)")
                lines.append(f"  `{error_msg}`")

        lines.append(f"\n_📅 {today.strftime('%d/%m/%Y')} — {datetime.now().strftime('%H:%M')}_")

        await _send("\n".join(lines))
        logger.info(f"Heartbeat inviato — {ok}/{total} feed OK, {s1+s2+s3} articoli")

    except Exception as e:
        logger.error(f"Errore heartbeat: {e}")
        await _send(f"❌ *Errore heartbeat*\n`{e}`")
    finally:
        session.close()


def _get_last_error(feed: FeedSource) -> str:
    if feed.notes and feed.notes.startswith("ERROR:"):
        return feed.notes[7:127]
    if feed.last_fetched_at and feed.last_success_at:
        delta = feed.last_fetched_at - feed.last_success_at
        hours = int(delta.total_seconds() / 3600)
        return f"Nessun fetch OK da {hours}h"
    return "Errore sconosciuto — controlla i log"
