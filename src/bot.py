"""
Bot handler — resta in ascolto dei comandi dell'admin via long polling.
Comandi supportati:
  /start    — messaggio di benvenuto
  /ok 1 3   — approva gli articoli nelle posizioni indicate
  /scarta 2 4 — scarta articoli fuori tema
  /status   — mostra lo stato della coda di oggi
  /analisi  — analisi keyword ultima settimana con suggerimenti
  /applica  — applica i suggerimenti keyword pendenti
  /ignora   — scarta i suggerimenti keyword pendenti
  /rollback — ripristina i pesi keyword all'ultima modifica
"""

import asyncio
import os
from collections import defaultdict
from datetime import date, timedelta
from time import time

import httpx
from dotenv import load_dotenv
from loguru import logger

from src.sender_telegram import (
    MAX_DAILY,
    PUBLISH_HOURS,
    _send,
    approve_articles,
)

# ── Rate limiting ──────────────────────────────────────────────
RATE_LIMIT_SECONDS = 5
_last_command_time: dict = defaultdict(float)

# Suggerimenti pendenti in attesa di /applica o /ignora
_pending_suggestions: list = []


def _is_rate_limited(chat_id: int) -> bool:
    now = time()
    if now - _last_command_time[chat_id] < RATE_LIMIT_SECONDS:
        return True
    _last_command_time[chat_id] = now
    return False


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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
                    params={
                        "offset": offset,
                        "timeout": 30,
                        "allowed_updates": ["message"],
                    },
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
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()

    if chat_id != ADMIN_ID:
        return

    if _is_rate_limited(chat_id):
        return

    if text == "/start":
        await _send(
            ADMIN_ID,
            (
                "👋 *Dritara Monitor attivo.*\n\n"
                "Ogni mattina riceverai la lista degli articoli selezionati.\n\n"
                "Comandi disponibili:\n"
                "• `/ok 1 3` — approva gli articoli nelle posizioni indicate\n"
                "• `/scarta 2 4` — scarta articoli fuori tema\n"
                "• `/status` — stato della coda di oggi\n"
                "• `/analisi` — analisi keyword ultima settimana\n"
                "• `/rollback` — ripristina pesi keyword all'ultima modifica"
            ),
        )
    elif text.startswith("/ok"):
        await _handle_ok(text)
    elif text.startswith("/scarta"):
        await _handle_scarta(text)
    elif text == "/status":
        await _handle_status()
    elif text == "/analisi":
        await _handle_analisi()
    elif text == "/applica":
        await _handle_applica()
    elif text == "/ignora":
        await _handle_ignora()
    elif text == "/rollback":
        await _handle_rollback()
    else:
        await _send(
            ADMIN_ID,
            "Comando non riconosciuto. Usa `/ok 1 3`, `/scarta 2 4`, `/status`, `/analisi` o `/rollback`.",
        )


async def _handle_ok(text: str) -> None:
    parts = text.split()[1:]

    if not parts:
        await _send(ADMIN_ID, "⚠️ Specifica i numeri degli articoli, es: `/ok 1 3`")
        return

    try:
        positions = [int(p) for p in parts]
    except ValueError:
        await _send(
            ADMIN_ID, "⚠️ Numeri non validi. Usa solo numeri interi, es: `/ok 1 3`"
        )
        return

    if len(positions) > MAX_DAILY:
        await _send(
            ADMIN_ID, f"⚠️ Puoi approvare al massimo {MAX_DAILY} articoli al giorno."
        )
        positions = positions[:MAX_DAILY]

    approved = approve_articles(positions, date.today())

    if approved == 0:
        await _send(ADMIN_ID, "⚠️ Nessun articolo trovato per le posizioni indicate.")
        return

    orari = [f"{PUBLISH_HOURS[i]}:00" for i in range(approved)]
    await _send(
        ADMIN_ID,
        (
            f"✅ *{approved} articoli approvati.*\n"
            f"Pubblicazione prevista: {' · '.join(orari)}\n"
            f"Ti avviserò prima di ogni pubblicazione."
        ),
    )
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

    emoji = {
        "pending": "⏳",
        "approved": "✅",
        "published": "📤",
        "deferred": "⏭️",
        "discarded": "🗑️",
    }
    lines = [f"📊 *Coda del {today.strftime('%d/%m/%Y')}*\n"]

    for q in queue:
        e = emoji.get(q.status, "•")
        ora = (
            f" — ore {q.scheduled_hour}:00"
            if q.scheduled_hour and q.status == "approved"
            else ""
        )
        lines.append(f"{e} #{q.position}{ora} — {q.status}")

    await _send(ADMIN_ID, "\n".join(lines))


async def _handle_scarta(text: str) -> None:
    from src.sender_telegram import discard_articles

    parts = text.split()[1:]

    if not parts:
        await _send(ADMIN_ID, "⚠️ Specifica i numeri degli articoli, es: `/scarta 2 4`")
        return

    try:
        positions = [int(p) for p in parts]
    except ValueError:
        await _send(
            ADMIN_ID, "⚠️ Numeri non validi. Usa solo numeri interi, es: `/scarta 2 4`"
        )
        return

    discarded = discard_articles(positions, date.today())

    if discarded == 0:
        await _send(ADMIN_ID, "⚠️ Nessun articolo trovato per le posizioni indicate.")
        return

    await _send(
        ADMIN_ID,
        (
            f"🗑️ *{discarded} articoli scartati.*\n"
            f"Non verranno pubblicati né riproposti nei giorni successivi."
        ),
    )
    logger.info(f"Admin ha scartato posizioni {positions}")


async def _handle_analisi() -> None:
    """Analizza keyword negli articoli approvati/scartati dell'ultima settimana."""
    global _pending_suggestions

    from sqlmodel import select

    from src.database import get_session
    from src.models import Article, KeywordConfig, PublishQueue

    session = next(get_session())
    oggi = date.today()
    una_settimana_fa = oggi - timedelta(days=7)

    # Recupera articoli approvati (published + approved) e scartati nell'ultima settimana
    approvati_ids = session.exec(
        select(PublishQueue.article_id)
        .where(PublishQueue.status.in_(["published", "approved"]))
        .where(PublishQueue.digest_date >= una_settimana_fa)
    ).all()

    scartati_ids = session.exec(
        select(PublishQueue.article_id)
        .where(PublishQueue.status == "discarded")
        .where(PublishQueue.digest_date >= una_settimana_fa)
    ).all()

    n_approvati = len(approvati_ids)
    n_scartati = len(scartati_ids)

    if n_approvati + n_scartati < 5:
        await _send(
            ADMIN_ID,
            (
                "📊 *Analisi keyword — ultima settimana*\n\n"
                f"Dati insufficienti: solo {n_approvati} approvati e {n_scartati} scartati.\n"
                "Servono almeno 5 articoli totali per un'analisi significativa.\n\n"
                "_Riprova tra qualche giorno quando ci saranno più dati._"
            ),
        )
        session.close()
        return

    # Conta occorrenze keyword per categoria
    def conta_keyword(article_ids: list) -> dict:
        counts: dict = defaultdict(int)
        if not article_ids:
            return counts
        articles = session.exec(
            select(Article).where(Article.id.in_(article_ids))
        ).all()
        for art in articles:
            if art.keyword_matches:
                for kw in art.keyword_matches:
                    counts[kw.lower()] += 1
        return counts

    kw_approvati = conta_keyword(approvati_ids)
    kw_scartati = conta_keyword(scartati_ids)

    # Recupera keyword attive dal DB
    keywords_db = session.exec(
        select(KeywordConfig).where(KeywordConfig.active == True)
    ).all()
    session.close()

    # Calcola tasso di approvazione per keyword
    tutte_le_kw = set(kw_approvati.keys()) | set(kw_scartati.keys())
    tassi: list = []
    for kw in tutte_le_kw:
        n_app = kw_approvati.get(kw, 0)
        n_sca = kw_scartati.get(kw, 0)
        totale = n_app + n_sca
        if totale == 0:
            continue
        tasso = n_app / totale
        tassi.append((kw, n_app, n_sca, totale, tasso))

    tassi.sort(key=lambda x: x[4], reverse=True)

    # Top keyword negli approvati (tasso > 70%, almeno 2 occorrenze)
    top_approvati = [
        (kw, n_app, n_sca, totale, tasso)
        for kw, n_app, n_sca, totale, tasso in tassi
        if tasso >= 0.7 and n_app >= 2
    ][:5]

    # Top keyword negli scartati (tasso < 30%, almeno 2 occorrenze)
    top_scartati = [
        (kw, n_app, n_sca, totale, tasso)
        for kw, n_app, n_sca, totale, tasso in tassi
        if tasso <= 0.3 and n_sca >= 2
    ][:5]

    # Genera suggerimenti
    suggerimenti: list = []
    kw_db_map = {k.keyword.lower(): k for k in keywords_db}

    for kw, n_app, n_sca, totale, tasso in top_approvati:
        if kw in kw_db_map:
            peso_attuale = kw_db_map[kw].weight
            nuovo_peso = min(round(peso_attuale + 0.5, 1), 3.0)
            if nuovo_peso > peso_attuale:
                suggerimenti.append(
                    {
                        "tipo": "aumenta_peso",
                        "keyword": kw,
                        "keyword_id": kw_db_map[kw].id,
                        "cluster": kw_db_map[kw].cluster,
                        "peso_attuale": peso_attuale,
                        "nuovo_peso": nuovo_peso,
                        "motivo": f"{n_app}/{totale} approvati ({int(tasso * 100)}%)",
                    }
                )

    for kw, n_app, n_sca, totale, tasso in top_scartati:
        if kw in kw_db_map:
            peso_attuale = kw_db_map[kw].weight
            nuovo_peso = max(round(peso_attuale - 0.5, 1), 0.5)
            if nuovo_peso < peso_attuale:
                suggerimenti.append(
                    {
                        "tipo": "riduci_peso",
                        "keyword": kw,
                        "keyword_id": kw_db_map[kw].id,
                        "cluster": kw_db_map[kw].cluster,
                        "peso_attuale": peso_attuale,
                        "nuovo_peso": nuovo_peso,
                        "motivo": f"{n_sca}/{totale} scartati ({int((1 - tasso) * 100)}%)",
                    }
                )

    # Componi messaggio
    lines = [
        "📊 *ANALISI KEYWORD — ultima settimana*",
        f"_{una_settimana_fa.strftime('%d/%m')} → {oggi.strftime('%d/%m/%Y')}_",
        f"Articoli approvati: *{n_approvati}* | Scartati: *{n_scartati}*\n",
    ]

    if top_approvati:
        lines.append("✅ *Keyword più frequenti negli APPROVATI:*")
        for kw, n_app, n_sca, totale, tasso in top_approvati:
            lines.append(f"  • {kw} → {n_app}/{totale} approvati ({int(tasso * 100)}%)")
        lines.append("")

    if top_scartati:
        lines.append("❌ *Keyword più frequenti negli SCARTATI:*")
        for kw, n_app, n_sca, totale, tasso in top_scartati:
            lines.append(
                f"  • {kw} → {n_sca}/{totale} scartati ({int((1 - tasso) * 100)}%)"
            )
        lines.append("")

    if not suggerimenti:
        lines.append("💡 *Nessun suggerimento:* i pesi attuali sembrano bilanciati.")
        await _send(ADMIN_ID, "\n".join(lines))
        return

    lines.append("💡 *SUGGERIMENTI:*")
    for i, s in enumerate(suggerimenti, 1):
        if s["tipo"] == "aumenta_peso":
            lines.append(
                f'  {i}. ⬆️ Aumenta peso *"{s["keyword"]}"* (Cluster {s["cluster"]}): '
                f"{s['peso_attuale']} → {s['nuovo_peso']}\n"
                f"     _Motivo: {s['motivo']}_"
            )
        else:
            lines.append(
                f'  {i}. ⬇️ Riduci peso *"{s["keyword"]}"* (Cluster {s["cluster"]}): '
                f"{s['peso_attuale']} → {s['nuovo_peso']}\n"
                f"     _Motivo: {s['motivo']}_"
            )

    lines.append("")
    lines.append("Rispondi `/applica` per confermare o `/ignora` per scartare.")

    _pending_suggestions = suggerimenti
    await _send(ADMIN_ID, "\n".join(lines))
    logger.info(f"Analisi keyword inviata — {len(suggerimenti)} suggerimenti")


async def _handle_applica() -> None:
    """Applica i suggerimenti keyword pendenti e salva la history per rollback."""
    global _pending_suggestions

    if not _pending_suggestions:
        await _send(
            ADMIN_ID, "⚠️ Nessun suggerimento pendente. Lancia prima `/analisi`."
        )
        return

    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig, KeywordWeightHistory

    session = next(get_session())
    applicati = []

    for s in _pending_suggestions:
        kw_row = session.exec(
            select(KeywordConfig)
            .where(KeywordConfig.keyword == s["keyword"])
            .where(KeywordConfig.active == True)
        ).first()

        if kw_row:
            vecchio = kw_row.weight

            # Salva history prima di modificare
            history = KeywordWeightHistory(
                keyword_id=kw_row.id,
                keyword=kw_row.keyword,
                cluster=kw_row.cluster,
                peso_precedente=vecchio,
                peso_nuovo=s["nuovo_peso"],
                motivo="analisi_automatica",
                applicato=True,
            )
            session.add(history)

            # Applica modifica
            kw_row.weight = s["nuovo_peso"]
            session.add(kw_row)

            applicati.append(f'  • "{s["keyword"]}": {vecchio} → {s["nuovo_peso"]}')

    session.commit()
    session.close()

    _pending_suggestions = []

    if not applicati:
        await _send(
            ADMIN_ID, "⚠️ Nessuna modifica applicata — keyword non trovate nel DB."
        )
        return

    lines = [
        "✅ *Modifiche applicate:*\n",
        *applicati,
        "",
        "_Le nuove soglie saranno attive dal prossimo fetch._",
        "_Usa `/rollback` per annullare queste modifiche._",
    ]
    await _send(ADMIN_ID, "\n".join(lines))
    logger.info(f"Applicati {len(applicati)} aggiornamenti keyword")


async def _handle_ignora() -> None:
    """Scarta i suggerimenti keyword pendenti."""
    global _pending_suggestions

    if not _pending_suggestions:
        await _send(ADMIN_ID, "⚠️ Nessun suggerimento pendente.")
        return

    n = len(_pending_suggestions)
    _pending_suggestions = []
    await _send(
        ADMIN_ID, f"🚫 *{n} suggerimenti ignorati.* I pesi rimangono invariati."
    )
    logger.info("Suggerimenti keyword ignorati dall'admin")


async def _handle_rollback() -> None:
    """Ripristina i pesi keyword all'ultima sessione di modifiche."""
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig, KeywordWeightHistory

    session = next(get_session())

    # Trova l'ultima sessione di modifiche (stesso minuto = stesso batch)
    ultima = session.exec(
        select(KeywordWeightHistory)
        .where(KeywordWeightHistory.applicato == True)
        .order_by(KeywordWeightHistory.modificato_at.desc())
    ).first()

    if not ultima:
        await _send(ADMIN_ID, "⚠️ Nessuna modifica precedente da annullare.")
        session.close()
        return

    # Prendi tutte le modifiche dello stesso batch (stessa sessione = stesso minuto)
    batch_time = ultima.modificato_at.replace(second=0, microsecond=0)
    batch = session.exec(
        select(KeywordWeightHistory)
        .where(KeywordWeightHistory.applicato == True)
        .where(KeywordWeightHistory.modificato_at >= batch_time)
    ).all()

    ripristinati = []

    for h in batch:
        kw_row = session.exec(
            select(KeywordConfig).where(KeywordConfig.id == h.keyword_id)
        ).first()

        if kw_row:
            kw_row.weight = h.peso_precedente
            session.add(kw_row)

        # Marca la history come annullata
        h.applicato = False
        session.add(h)

        ripristinati.append(
            f'  • "{h.keyword}": {h.peso_nuovo} → {h.peso_precedente} _(ripristinato)_'
        )

    session.commit()
    session.close()

    if not ripristinati:
        await _send(ADMIN_ID, "⚠️ Nessuna modifica da annullare.")
        return

    lines = [
        "↩️ *Rollback completato:*\n",
        *ripristinati,
        "",
        "_I pesi originali sono stati ripristinati._",
    ]
    await _send(ADMIN_ID, "\n".join(lines))
    logger.info(f"Rollback eseguito — {len(ripristinati)} keyword ripristinate")
