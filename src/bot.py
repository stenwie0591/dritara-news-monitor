"""
Bot handler — resta in ascolto dei comandi dell'admin via long polling.
Comandi supportati:
  /start   — messaggio di benvenuto
  /ok 1 3  — approva gli articoli nelle posizioni indicate
  /status  — mostra lo stato della coda di oggi
"""
import asyncio
import os
from datetime import date

import httpx
from dotenv import load_dotenv
from loguru import logger

from src.sender_telegram import (
    MAX_DAILY,
    PUBLISH_HOURS,
    approve_articles,
    get_next_to_publish,
    mark_published,
    publish_article,
    _send,
)

load_dotenv()

TOKEN    = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID"))
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


async def run_bot() -> None:
    """Avvia il bot in long polling."""
    logger.info("Bot avviato — in ascolto comandi admin")
    offset = 0

    async with httpx.AsyncClient(timeout=35) as client:
        while True:
            try:
                r = await client.get(
                    f"{BASE_URL}/getUpdates",
                    params={"offset": offset, "timeout": 30, "allowed_updates": ["message"]},
                )
                updates = r.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    await _handle(update)
            except asyncio.CancelledError:
                logger.info("Bot interrotto")
                break
            except Exception as e:
                logger.error(f"Errore polling: {e}")
                await asyncio.sleep(5)


async def _handle(update: dict) -> None:
    msg     = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text    = msg.get("text", "").strip()

    if chat_id != ADMIN_ID:
        return

    if text == "/start":
        await _send(ADMIN_ID, (
            "👋 *Dritara Monitor attivo.*\n\n"
            "Ogni mattina riceverai la lista degli articoli selezionati.\n"
            "Rispondi con `/ok` seguito dai numeri per approvarli, es: `/ok 1 3`\n"
            "Usa `/status` per vedere lo stato della coda di oggi."
        ))
    elif text.startswith("/ok"):
        await _handle_ok(text)
    elif text == "/status":
        await _handle_status()
    else:
        await _send(ADMIN_ID, "Comando non riconosciuto. Usa `/ok 1 3` oppure `/status`.")


async def _handle_ok(text: str) -> None:
    parts = text.split()[1:]

    if not parts:
        await _send(ADMIN_ID, "⚠️ Specifica i numeri degli articoli, es: `/ok 1 3`")
        return

    try:
        positions = [int(p) for p in parts]
    except ValueError:
        await _send(ADMIN_ID, "⚠️ Numeri non validi. Usa solo numeri interi, es: `/ok 1 3`")
        return

    if len(positions) > MAX_DAILY:
        await _send(ADMIN_ID, f"⚠️ Puoi approvare al massimo {MAX_DAILY} articoli al giorno.")
        positions = positions[:MAX_DAILY]

    approved = approve_articles(positions, date.today())

    if approved == 0:
        await _send(ADMIN_ID, "⚠️ Nessun articolo trovato per le posizioni indicate.")
        return

    # Mostra orari assegnati
    orari = [f"{PUBLISH_HOURS[i]}:00" for i in range(approved)]
    await _send(ADMIN_ID, (
        f"✅ *{approved} articoli approvati.*\n"
        f"Pubblicazione prevista: {' · '.join(orari)}\n"
        f"Ti avviserò prima di ogni pubblicazione."
    ))
    logger.info(f"Admin ha approvato posizioni {positions}")


async def _handle_status() -> None:
    from sqlmodel import select
    from src.database import get_session
    from src.models import PublishQueue

    session = next(get_session())
    today = date.today()

    queue = session.exec(
        select(PublishQueue)
        .where(PublishQueue.digest_date == today)
        .order_by(PublishQueue.position)
    ).all()
    session.close()

    if not queue:
        await _send(ADMIN_ID, "📭 Nessun articolo in coda per oggi.")
        return

    emoji = {"pending": "⏳", "approved": "✅", "published": "📤", "deferred": "⏭️", "discarded": "🗑️"}
    lines = [f"📊 *Coda del {today.strftime('%d/%m/%Y')}*\n"]

    for q in queue:
        e = emoji.get(q.status, "•")
        ora = f" — ore {q.scheduled_hour}:00" if q.scheduled_hour and q.status == "approved" else ""
        lines.append(f"{e} #{q.position}{ora} — {q.status}")

    await _send(ADMIN_ID, "\n".join(lines))
