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

# Orari in ordine di priorità
PUBLISH_HOURS = [18, 13, 9, 22]
MAX_DAILY = 4
MAX_DEFERRALS = 4


# ── API Telegram ───────────────────────────────────────────────
async def _send(
    chat_id: int, text: str, thread_id: Optional[int] = None
) -> Optional[int]:
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
    """
    Manda all'admin la lista articoli del giorno.
    Prima mostra i deferred del giorno precedente, poi i nuovi.
    """
    # Carica deferred dei giorni precedenti
    deferred = _get_deferred_articles()

    if not articles and not deferred:
        await _send(ADMIN_ID, "📭 Nessun articolo disponibile oggi.")
        return

    lines = []
    lines.append(f"📋 *DRITARA — Articoli del {digest_date.strftime('%d/%m/%Y')}*")
    lines.append(
        f"Rispondi con `/ok` seguito dai numeri (max {MAX_DAILY}), es: `/ok 1 3`\n"
    )

    all_articles = []

    # Prima i deferred (con etichetta)
    if deferred:
        lines.append("*⏭️ In attesa dai giorni precedenti:*")
        for item in deferred:
            a = item["article"]
            count = item["deferred_count"]
            all_articles.append(
                {"source": "deferred", "queue_id": item["queue_id"], **a}
            )
            i = len(all_articles)
            lines.append(
                f"*{i}.* [{a['title']}]({a['url']})\n"
                f"   _{a['feed_name']} · score {a['score']:.1f} · rimandato {count}x_\n"
            )

    # Poi i nuovi
    if articles:
        if deferred:
            lines.append("*🆕 Nuovi di oggi:*")
        for a in articles:
            all_articles.append({"source": "new", **a})
            i = len(all_articles)
            lines.append(
                f"*{i}.* [{a['title']}]({a['url']})\n"
                f"   _{a['feed_name']} · score {a['score']:.1f}_\n"
            )

    # Salva tutti in pending
    _save_pending(all_articles, digest_date)

    text = "\n".join(lines)
    if len(text) > 4096:
        mid = text.rfind("\n", 0, 4096)
        await _send(ADMIN_ID, text[:mid])
        await _send(ADMIN_ID, text[mid:])
    else:
        await _send(ADMIN_ID, text)

    logger.info(f"Notifica admin — {len(deferred)} deferred + {len(articles)} nuovi")


# ── Pubblicazione nel topic ────────────────────────────────────
async def publish_article(article: dict) -> bool:
    title = article.get("title", "")
    excerpt = article.get("excerpt", "")
    source = article.get("feed_name", "")
    url = article.get("url", "")

    short_excerpt = ""
    if excerpt:
        short_excerpt = (
            excerpt[:200].rsplit(" ", 1)[0] + "…" if len(excerpt) > 200 else excerpt
        )

    lines = []
    lines.append(f"*{title}*")
    if short_excerpt:
        lines.append(f"\n_{short_excerpt}_")
    lines.append(f"\n[Leggi su {source}]({url})")

    # Avvisa admin prima di pubblicare nel topic
    await _send(ADMIN_ID, f"📤 Sto pubblicando nel topic:\n*{title[:80]}*")
    msg_id = await _send(COMMUNITY_ID, "\n".join(lines), thread_id=THREAD_ID)

    if msg_id:
        logger.info(f"Pubblicato nel topic: {title[:60]}...")
        return True
    return False


# ── Coda pubblicazione ─────────────────────────────────────────
def _get_deferred_articles() -> list[dict]:
    """
    Recupera gli articoli deferred dei giorni precedenti
    con deferred_count < MAX_DEFERRALS.
    """
    session = next(get_session())
    today = date.today()

    queue = session.exec(
        select(PublishQueue)
        .where(
            PublishQueue.digest_date < today,
            PublishQueue.status == "deferred",
            PublishQueue.deferred_count < MAX_DEFERRALS,
        )
        .order_by(PublishQueue.deferred_count.desc(), PublishQueue.position)
    ).all()

    result = []
    for q in queue:
        article = session.get(Article, q.article_id)
        if article:
            result.append(
                {
                    "queue_id": q.id,
                    "deferred_count": q.deferred_count,
                    "article": {
                        "id": article.id,
                        "title": article.title,
                        "excerpt": article.excerpt,
                        "feed_name": article.feed_name,
                        "url": article.url,
                        "score": article.score,
                    },
                }
            )

    session.close()
    return result


def _save_pending(articles: list[dict], digest_date: date) -> None:
    """Salva articoli in coda pending per oggi."""
    session = next(get_session())

    # Rimuovi pending precedenti per oggi
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
        # Se è un deferred, aggiorna il record originale
        if a.get("source") == "deferred" and a.get("queue_id"):
            original = session.get(PublishQueue, a["queue_id"])
            if original:
                original.digest_date = digest_date
                original.position = i
                original.status = "pending"
                session.add(original)
        else:
            q = PublishQueue(
                article_id=a["id"],
                digest_date=digest_date,
                position=i,
                status="pending",
                deferred_count=0,
            )
            session.add(q)

    session.commit()
    session.close()
    logger.info(f"Salvati {len(articles)} articoli in coda pending")


def approve_articles(positions: list[int], digest_date: date) -> int:
    """Approva le posizioni indicate, rimanda il resto."""
    session = next(get_session())
    approved = 0

    # Assegna orari in base alla priorità
    hours = PUBLISH_HOURS[: len(positions)]

    for idx, pos in enumerate(positions[:MAX_DAILY]):
        q = session.exec(
            select(PublishQueue).where(
                PublishQueue.digest_date == digest_date,
                PublishQueue.position == pos,
                PublishQueue.status == "pending",
            )
        ).first()
        if q:
            q.status = "approved"
            q.scheduled_hour = hours[idx] if idx < len(hours) else PUBLISH_HOURS[-1]
            session.add(q)
            approved += 1

    # Gli altri → deferred, incrementa contatore
    pending = session.exec(
        select(PublishQueue).where(
            PublishQueue.digest_date == digest_date,
            PublishQueue.status == "pending",
        )
    ).all()
    for p in pending:
        p.deferred_count += 1
        if p.deferred_count >= MAX_DEFERRALS:
            p.status = "discarded"
            logger.info(
                f"Articolo scartato dopo {MAX_DEFERRALS} deferrals: {p.article_id[:16]}..."
            )
        else:
            p.status = "deferred"
        session.add(p)

    session.commit()
    session.close()
    logger.info(f"Approvati {approved} articoli, resto rimandato")
    return approved


def get_next_to_publish(publish_date: date, hour: int) -> Optional[dict]:
    """Ritorna l'articolo approvato per l'ora indicata."""
    session = next(get_session())

    q = session.exec(
        select(PublishQueue).where(
            PublishQueue.digest_date == publish_date,
            PublishQueue.status == "approved",
            PublishQueue.scheduled_hour == hour,
        )
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


def discard_articles(positions: list[int], digest_date: date) -> int:
    """
    Scarta manualmente gli articoli nelle posizioni indicate.
    Li segna come 'discarded' così non riappaiono nei giorni successivi.
    """
    session = next(get_session())
    discarded = 0

    for pos in positions:
        q = session.exec(
            select(PublishQueue).where(
                PublishQueue.digest_date == digest_date,
                PublishQueue.position == pos,
                PublishQueue.status == "pending",
            )
        ).first()
        if q:
            q.status = "discarded"
            session.add(q)
            discarded += 1

    session.commit()
    session.close()
    logger.info(f"Scartati manualmente {discarded} articoli alle posizioni {positions}")
    return discarded
