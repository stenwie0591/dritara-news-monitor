import asyncio
import os
from datetime import date, datetime
from typing import Optional

import httpx
from dotenv import load_dotenv
from loguru import logger
from sqlmodel import select

from src.database import get_session
from src.models import Article, PublishQueue

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID"))
COMMUNITY_ID = int(os.getenv("TELEGRAM_COMMUNITY_CHAT_ID"))
THREAD_ID = int(os.getenv("TELEGRAM_NEWS_THREAD_ID"))

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

PUBLISH_HOURS = [9, 13, 18, 22]
MAX_DAILY = 4


# ── API Telegram ───────────────────────────────────────────────
async def _send(chat_id: int, text: str, thread_id: Optional[int] = None) -> Optional[int]:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    if thread_id:
        payload["message_thread_id"] = thread_id

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["result"]["message_id"]
        else:
            logger.error(f"Telegram error: {data}")
            return None


# ── Notifica admin ─────────────────────────────────────────────
async def notify_admin(articles: list[dict], digest_date: date) -> None:
    if not articles:
        await _send(ADMIN_ID, "📭 Nessun articolo in Sezione 1 oggi.")
        return

    lines = []
    lines.append(f"📋 *DRITARA — Articoli del {digest_date.strftime('%d/%m/%Y')}*")
    lines.append(f"Seleziona quali pubblicare oggi (max {MAX_DAILY}).")
    lines.append(f"Rispondi con `/ok` seguito dai numeri, es: `/ok 1 3`\n")

    for i, a in enumerate(articles, 1):
        score = a.get("score", 0)
        source = a.get("feed_name", "")
        title = a.get("title", "")
        url = a.get("url", "")
        lines.append(f"*{i}.* [{title}]({url})\n   _{source} · score {score:.1f}_\n")

    _save_pending(articles, digest_date)

    text = "\n".join(lines)
    if len(text) > 4096:
        mid = text.rfind("\n", 0, 4096)
        await _send(ADMIN_ID, text[:mid])
        await _send(ADMIN_ID, text[mid:])
    else:
        await _send(ADMIN_ID, text)

    logger.info(f"Notifica admin inviata — {len(articles)} articoli in lista")


# ── Pubblicazione nel topic ────────────────────────────────────
async def publish_article(article: dict) -> bool:
    title   = article.get("title", "")
    excerpt = article.get("excerpt", "")
    source  = article.get("feed_name", "")
    url     = article.get("url", "")

    short_excerpt = ""
    if excerpt:
        short_excerpt = excerpt[:200].rsplit(" ", 1)[0] + "…" if len(excerpt) > 200 else excerpt

    lines = []
    lines.append(f"*{title}*")
    if short_excerpt:
        lines.append(f"\n_{short_excerpt}_")
    lines.append(f"\n[Leggi su {source}]({url})")

    text = "\n".join(lines)
    msg_id = await _send(COMMUNITY_ID, text, thread_id=THREAD_ID)

    if msg_id:
        logger.info(f"Pubblicato nel topic: {title[:60]}...")
        return True
    return False


# ── Coda pubblicazione ─────────────────────────────────────────
def _save_pending(articles: list[dict], digest_date: date) -> None:
    session = next(get_session())
    existing = session.exec(
        select(PublishQueue).where(
            PublishQueue.digest_date == digest_date,
            PublishQueue.status == "pending",
        )
    ).all()
    for e in existing:
        session.delete(e)
    session.commit()

    for i, a in enumerate(articles, 1):
        q = PublishQueue(
            article_id=a["id"],
            digest_date=digest_date,
            position=i,
            status="pending",
        )
        session.add(q)
    session.commit()
    session.close()
    logger.info(f"Salvati {len(articles)} articoli in coda pending")


def approve_articles(positions: list[int], digest_date: date) -> int:
    session = next(get_session())
    approved = 0

    for pos in positions[:MAX_DAILY]:
        q = session.exec(
            select(PublishQueue).where(
                PublishQueue.digest_date == digest_date,
                PublishQueue.position == pos,
                PublishQueue.status == "pending",
            )
        ).first()
        if q:
            q.status = "approved"
            session.add(q)
            approved += 1

    pending = session.exec(
        select(PublishQueue).where(
            PublishQueue.digest_date == digest_date,
            PublishQueue.status == "pending",
        )
    ).all()
    for p in pending:
        p.status = "deferred"
        session.add(p)

    session.commit()
    session.close()
    logger.info(f"Approvati {approved} articoli, resto rimandato a domani")
    return approved


def get_next_to_publish(publish_date: date) -> Optional[dict]:
    session = next(get_session())
    q = session.exec(
        select(PublishQueue).where(
            PublishQueue.digest_date == publish_date,
            PublishQueue.status == "approved",
        ).order_by(PublishQueue.position)
    ).first()

    if not q:
        session.close()
        return None

    article = session.get(Article, q.article_id)
    session.close()

    if not article:
        return None

    return {
        "queue_id": q.id,
        "id": article.id,
        "title": article.title,
        "excerpt": article.excerpt,
        "feed_name": article.feed_name,
        "url": article.url,
        "score": article.score,
        "section": article.section,
    }


def mark_published(queue_id: int) -> None:
    session = next(get_session())
    q = session.get(PublishQueue, queue_id)
    if q:
        q.status = "published"
        q.published_at = datetime.utcnow()
        session.add(q)
        session.commit()
    session.close()
