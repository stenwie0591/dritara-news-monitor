from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Optional

import httpx
from loguru import logger
from sqlmodel import select

from src.config import RuntimeSettings, get_settings
from src.database import get_session
from src.models import Article, PublishQueue
from src.telegram_renderer import HtmlFragment, TelegramMessage, telegram_renderer

# Orari in ordine di priorità
PUBLISH_HOURS = [9, 13, 18, 22]
MAX_DAILY = 4
MAX_DEFERRALS = 4


def _is_already_published(title: str, session, days: int = 7) -> bool:
    """Controlla se un articolo simile è già stato pubblicato negli ultimi N giorni."""
    cutoff = date.today() - timedelta(days=days)
    published = session.exec(
        select(PublishQueue).where(
            PublishQueue.status == "published",
            PublishQueue.published_at >= datetime.combine(cutoff, datetime.min.time()),
        )
    ).all()
    for q in published:
        article = session.get(Article, q.article_id)
        if article:
            ratio = SequenceMatcher(None, title.lower(), article.title.lower()).ratio()
            if ratio >= 0.85:
                logger.debug(f"Già pubblicato ({ratio:.0%}): {title[:60]}")
                return True
    return False


# ── API Telegram ───────────────────────────────────────────────
async def _send(
    chat_id: int,
    text: str | TelegramMessage,
    thread_id: Optional[int] = None,
    *,
    settings: RuntimeSettings | None = None,
) -> Optional[int]:
    runtime = (settings or get_settings()).validated_for_runtime()
    messages = [text] if isinstance(text, TelegramMessage) else telegram_renderer.plain_messages(text)
    last_message_id: Optional[int] = None
    async with httpx.AsyncClient() as client:
        base_url = f"https://api.telegram.org/bot{runtime.telegram_token_value}"
        for message in messages:
            payload = {
                "chat_id": chat_id,
                "text": message.text,
                "parse_mode": message.parse_mode,
                "disable_web_page_preview": False,
            }
            if thread_id:
                payload["message_thread_id"] = thread_id
            response = await client.post(
                f"{base_url}/sendMessage", json=payload, timeout=10
            )
            data = response.json()
            if not data.get("ok"):
                logger.error(f"Telegram error: {data}")
                return None
            last_message_id = data["result"]["message_id"]
    return last_message_id


# ── Notifica admin ─────────────────────────────────────────────
async def notify_admin(
    articles_s1: list[dict],
    digest_date: date,
    articles_s2: Optional[list[dict]] = None,
    *,
    settings: RuntimeSettings | None = None,
) -> None:
    """
    Manda all'admin la lista articoli del giorno.
    Ordine: deferred → section1 (🔴) → section2 top 5 (🟡)
    Max 1 articolo per feed sull'intera lista.
    """
    runtime = (settings or get_settings()).validated_for_runtime()
    admin_id = runtime.telegram_admin_chat_id or 0
    articles_s2 = articles_s2 or []
    deferred = _get_deferred_articles()

    if not articles_s1 and not articles_s2 and not deferred:
        await _send(
            admin_id,
            telegram_renderer.message("📭 Nessun articolo disponibile oggi."),
            settings=runtime,
        )
        return

    lines: list[HtmlFragment] = []
    lines.append(
        telegram_renderer.join(
            "📋 ",
            telegram_renderer.bold(
                f"DRITARA — Articoli del {digest_date.strftime('%d/%m/%Y')}"
            ),
        )
    )
    lines.append(
        telegram_renderer.join(
            "Rispondi con ",
            telegram_renderer.code("/ok"),
            f" seguito dai numeri (max {MAX_DAILY}), es: ",
            telegram_renderer.code("/ok 1 3"),
            "\n",
        )
    )

    all_articles = []

    # ── Deferred ───────────────────────────────────────────────
    if deferred:
        lines.append(telegram_renderer.bold("⏭️ In attesa dai giorni precedenti:"))
        for item in deferred:
            a = item["article"]
            count = item["deferred_count"]
            all_articles.append(
                {"source": "deferred", "queue_id": item["queue_id"], **a}
            )
            i = len(all_articles)
            lines.append(
                telegram_renderer.join(
                    telegram_renderer.bold(f"{i}."),
                    " ",
                    telegram_renderer.link(a["title"], a["url"], label_limit=300),
                    "\n   ",
                    telegram_renderer.italic(
                        f"{a['feed_name']} · score {a['score']:.1f} · rimandato {count}x",
                        limit=400,
                    ),
                    "\n",
                )
            )

    # ── Filtra già pubblicati + max 1 per feed ─────────────────
    session = next(get_session())

    MAX_PER_FEED = 1
    feed_counts: dict = {}

    def _filter(articles: list[dict]) -> list[dict]:
        result = []
        for a in articles:
            if _is_already_published(a["title"], session):
                continue
            feed = a["feed_name"]
            feed_counts[feed] = feed_counts.get(feed, 0) + 1
            if feed_counts[feed] <= MAX_PER_FEED:
                result.append(a)
            else:
                logger.debug(f"Feed limit ({MAX_PER_FEED}): {a['title'][:60]}")
        return result

    articles_s1 = _filter(articles_s1)
    articles_s2 = _filter(articles_s2)
    session.close()

    # ── Section1 🔴 ────────────────────────────────────────────
    if articles_s1:
        if deferred:
            lines.append(telegram_renderer.bold("🆕 Nuovi di oggi:"))
        lines.append(telegram_renderer.bold("🔴 Sud + Tech:"))
        for a in articles_s1:
            all_articles.append({"source": "new", **a})
            i = len(all_articles)
            lines.append(
                telegram_renderer.join(
                    telegram_renderer.bold(f"{i}."),
                    " ",
                    telegram_renderer.link(a["title"], a["url"], label_limit=300),
                    "\n   ",
                    telegram_renderer.italic(
                        f"{a['feed_name']} · score {a['score']:.1f}", limit=400
                    ),
                    "\n",
                )
            )

    # ── Section2 🟡 top 5 ──────────────────────────────────────
    if articles_s2:
        lines.append(telegram_renderer.bold("🟡 Trend nazionali:"))
        for a in articles_s2[:5]:
            all_articles.append({"source": "new", **a})
            i = len(all_articles)
            lines.append(
                telegram_renderer.join(
                    telegram_renderer.bold(f"{i}."),
                    " ",
                    telegram_renderer.link(a["title"], a["url"], label_limit=300),
                    "\n   ",
                    telegram_renderer.italic(
                        f"{a['feed_name']} · score {a['score']:.1f}", limit=400
                    ),
                    "\n",
                )
            )

    # ── Salva in pending ───────────────────────────────────────
    _save_pending(all_articles, digest_date)

    for message in telegram_renderer.split_lines(lines):
        await _send(admin_id, message, settings=runtime)

    logger.info(
        f"Notifica admin — {len(deferred)} deferred + "
        f"{len(articles_s1)} s1 + {len(articles_s2[:5])} s2"
    )


# ── Pubblicazione nel topic ────────────────────────────────────
async def publish_article(
    article: dict, *, settings: RuntimeSettings | None = None
) -> bool:
    title = article.get("title", "")
    excerpt = article.get("excerpt", "")
    source = article.get("feed_name", "")
    url = article.get("url", "")

    short_excerpt = ""
    if excerpt:
        short_excerpt = (
            excerpt[:200].rsplit(" ", 1)[0] + "…" if len(excerpt) > 200 else excerpt
        )

    lines: list[HtmlFragment] = []
    lines.append(telegram_renderer.bold(title, limit=300))
    if short_excerpt:
        lines.append(telegram_renderer.italic(short_excerpt, limit=220))
    lines.append(
        telegram_renderer.link(f"Leggi su {source}", url, label_limit=400)
    )

    # Avvisa admin prima di pubblicare nel topic
    runtime = (settings or get_settings()).validated_for_runtime()
    admin_id = runtime.telegram_admin_chat_id or 0
    community_id = runtime.telegram_community_chat_id or 0
    thread_id = runtime.telegram_news_thread_id or 0
    await _send(
        admin_id,
        telegram_renderer.message(
            "📤 Sto pubblicando nel topic:\n",
            telegram_renderer.bold(title, limit=80),
        ),
        settings=runtime,
    )
    message = telegram_renderer.split_lines(lines)[0]
    msg_id = await _send(community_id, message, thread_id=thread_id, settings=runtime)

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
            already_queued = session.exec(
                select(PublishQueue).where(
                    PublishQueue.article_id == a["id"],
                    PublishQueue.digest_date == digest_date,
                )
            ).first()
            if already_queued:
                logger.warning(
                    "Coda idempotente: articolo già presente per il digest corrente"
                )
                continue
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
        q.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(q)
        session.commit()
    session.close()


def mark_publishing(queue_id: int) -> None:
    """Segna l'articolo come 'publishing' prima dell'invio — previene doppio invio."""
    session = next(get_session())
    q = session.get(PublishQueue, queue_id)
    if q:
        q.status = "publishing"
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


async def alert_feed_errors(
    feed_errors: list[dict], *, settings: RuntimeSettings | None = None
) -> None:
    """
    Invia alert immediato all'admin per feed con errori critici
    (consecutive_errors >= 3).
    """
    session = next(get_session())
    critical: list[HtmlFragment] = []

    for fe in feed_errors:
        from src.models import FeedSource

        source = session.exec(
            select(FeedSource).where(FeedSource.id == fe["source_id"])
        ).first()
        if source and source.consecutive_errors >= 3:
            critical.append(
                telegram_renderer.join(
                    "• ",
                    telegram_renderer.bold(source.name, limit=200),
                    f" — {source.consecutive_errors} errori consecutivi\n  ",
                    telegram_renderer.code(fe["error"], limit=80),
                )
            )

    session.close()

    if not critical:
        return

    lines: list[HtmlFragment] = [
        telegram_renderer.join(
            "⚠️ ", telegram_renderer.bold("DRITARA — Alert feed critici"), "\n"
        )
    ]
    lines.extend(critical)
    runtime = (settings or get_settings()).validated_for_runtime()
    for message in telegram_renderer.split_lines(lines):
        await _send(runtime.telegram_admin_chat_id or 0, message, settings=runtime)
    logger.warning(f"Alert inviato per {len(critical)} feed critici")
