"""
Bot handler — resta in ascolto dei comandi dell'admin via long polling.
Comandi supportati:
  /start        — messaggio di benvenuto
  /ok 1 3       — approva gli articoli nelle posizioni indicate
  /scarta 2 4   — scarta articoli fuori tema
  /status       — mostra lo stato della coda di oggi
  /analisi      — analisi keyword ultima settimana con suggerimenti
  /applica      — applica i suggerimenti keyword pendenti
  /ignora       — scarta i suggerimenti keyword pendenti
  /rollback     — ripristina i pesi keyword all'ultima modifica

  /feedlist                    — lista feed con stato e statistiche
  /feedadd <url> <nome> <liv>  — aggiunge nuovo feed RSS (con verifica)
  /feeddisable <id>            — disattiva feed
  /feedenable <id>             — riattiva feed

  /kwlist                      — lista keyword per cluster
  /kwadd <cluster> <peso> <kw> — aggiunge nuova keyword
  /kwremove <keyword>          — rimuove keyword definitivamente
  /kwset <keyword> <peso>      — modifica peso keyword
"""

import asyncio
import os
from collections import defaultdict
from datetime import date, timedelta
from time import time

import feedparser
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
                "*Comandi editoriali:*\n"
                "• `/ok 1 3` — approva articoli nelle posizioni indicate\n"
                "• `/scarta 2 4` — scarta articoli fuori tema\n"
                "• `/status` — stato della coda di oggi\n\n"
                "*Comandi keyword:*\n"
                "• `/analisi` — analisi keyword ultima settimana\n"
                "• `/applica` — applica suggerimenti pendenti\n"
                "• `/ignora` — scarta suggerimenti pendenti\n"
                "• `/rollback` — ripristina pesi all'ultima modifica\n"
                "• `/kwlist` — lista keyword per cluster\n"
                "• `/kwadd A 1.5 robotica` — aggiunge keyword\n"
                "• `/kwremove robotica` — rimuove keyword\n"
                "• `/kwset robotica 2.0` — modifica peso keyword\n\n"
                "*Comandi feed:*\n"
                "• `/feedlist` — lista feed con statistiche\n"
                "• `/feedadd <url> <nome> <livello>` — aggiunge feed\n"
                "• `/feeddisable <id>` — disattiva feed\n"
                "• `/feedenable <id>` — riattiva feed"
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
    elif text == "/feedlist":
        await _handle_feedlist()
    elif text.startswith("/feedadd"):
        await _handle_feedadd(text)
    elif text.startswith("/feeddisable"):
        await _handle_feeddisable(text)
    elif text.startswith("/feedenable"):
        await _handle_feedenable(text)
    elif text == "/kwlist":
        await _handle_kwlist()
    elif text.startswith("/kwadd"):
        await _handle_kwadd(text)
    elif text.startswith("/kwremove"):
        await _handle_kwremove(text)
    elif text.startswith("/kwset"):
        await _handle_kwset(text)
    else:
        await _send(
            ADMIN_ID,
            "Comando non riconosciuto. Usa `/start` per vedere tutti i comandi disponibili.",
        )


# ── Comandi editoriali ─────────────────────────────────────────


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
    from src.models import Article, PublishQueue

    session = next(get_session())
    today = date.today()

    queue = session.exec(
        select(PublishQueue)
        .where(PublishQueue.digest_date == today)
        .order_by(PublishQueue.position)
    ).all()

    emoji = {
        "pending": "⏳",
        "approved": "✅",
        "published": "📤",
        "deferred": "⏭️",
        "discarded": "🗑️",
    }
    lines = [f"📊 *Coda del {today.strftime('%d/%m/%Y')}*\n"]

    for q in queue:
        article = session.get(Article, q.article_id)
        titolo = article.title[:50] if article else "?"
        e = emoji.get(q.status, "•")
        ora = (
            f" — ore {q.scheduled_hour}:00"
            if q.scheduled_hour and q.status == "approved"
            else ""
        )
        lines.append(f"{e} #{q.position}{ora} — _{titolo}_")

    session.close()

    if not queue:
        await _send(ADMIN_ID, "📭 Nessun articolo in coda per oggi.")
        return

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


# ── Comandi feed ───────────────────────────────────────────────


async def _handle_feedlist() -> None:
    from sqlmodel import select

    from src.database import get_session
    from src.models import FeedSource, FeedStats

    session = next(get_session())
    feeds = session.exec(
        select(FeedSource).order_by(FeedSource.level, FeedSource.name)
    ).all()

    if not feeds:
        await _send(ADMIN_ID, "📭 Nessun feed configurato.")
        session.close()
        return

    # Statistiche ultime 7 giorni per feed
    oggi = date.today()
    sette_giorni_fa = oggi - timedelta(days=7)
    stats_rows = session.exec(
        select(FeedStats).where(FeedStats.fetch_date >= sette_giorni_fa)
    ).all()

    stats_map: dict = defaultdict(lambda: {"fetched": 0, "relevant": 0})
    for s in stats_rows:
        stats_map[s.feed_source_id]["fetched"] += s.articles_fetched
        stats_map[s.feed_source_id]["relevant"] += s.articles_relevant

    session.close()

    lines = ["📡 *FEED CONFIGURATI*\n"]
    current_level = None

    for f in feeds:
        if f.level != current_level:
            current_level = f.level
            label = {
                1: "Livello 1 — Nazionali tech",
                2: "Livello 2 — Regionali/tematici",
                3: "Livello 3 — Locali",
            }.get(f.level, f"Livello {f.level}")
            lines.append(f"\n*{label}:*")

        stato = "🟢" if f.active else "🔴"
        s = stats_map[f.id]
        stats_str = (
            f"{s['relevant']}/{s['fetched']} rilevanti (7gg)"
            if s["fetched"] > 0
            else "nessun dato"
        )
        lines.append(f"{stato} `[{f.id}]` *{f.name}* — {stats_str}")

    lines.append("\n_Usa `/feeddisable <id>` o `/feedenable <id>` per gestire i feed._")
    await _send(ADMIN_ID, "\n".join(lines))


async def _handle_feedadd(text: str) -> None:

    from src.database import get_session
    from src.models import FeedSource

    parts = text.split(maxsplit=3)
    if len(parts) < 4:
        await _send(
            ADMIN_ID,
            "⚠️ Sintassi: `/feedadd <url> <nome> <livello>`\n"
            "Esempio: `/feedadd https://example.com/rss.xml Example Feed 2`",
        )
        return

    _, url, nome, livello_str = parts
    livello_str = livello_str.strip()

    # Valida livello
    try:
        livello = int(livello_str)
        if livello not in (1, 2, 3):
            raise ValueError
    except ValueError:
        await _send(ADMIN_ID, "⚠️ Il livello deve essere 1, 2 o 3.")
        return

    # Verifica che il feed RSS sia valido
    await _send(ADMIN_ID, f"🔄 Verifico il feed `{url}`...")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, follow_redirects=True)
            r.raise_for_status()
            parsed = feedparser.parse(r.text)
            if parsed.bozo and not parsed.entries:
                await _send(
                    ADMIN_ID, f"⚠️ URL non riconosciuto come feed RSS valido.\n`{url}`"
                )
                return
            n_entries = len(parsed.entries)
    except Exception as e:
        await _send(ADMIN_ID, f"⚠️ Impossibile raggiungere il feed:\n`{e}`")
        return

    # Salva nel DB
    session = next(get_session())
    try:
        from sqlmodel import select

        existing = session.exec(select(FeedSource).where(FeedSource.url == url)).first()
        if existing:
            await _send(ADMIN_ID, f"⚠️ Feed già presente nel DB con id `{existing.id}`.")
            session.close()
            return

        feed = FeedSource(
            name=nome,
            url=url,
            level=livello,
            active=True,
        )
        session.add(feed)
        session.commit()
        session.refresh(feed)
        feed_id = feed.id
    except Exception as e:
        await _send(ADMIN_ID, f"⚠️ Errore salvataggio: `{e}`")
        session.close()
        return
    session.close()

    await _send(
        ADMIN_ID,
        (
            f"✅ *Feed aggiunto con successo.*\n"
            f"ID: `{feed_id}` | Nome: *{nome}* | Livello: {livello}\n"
            f"Feed valido — trovati {n_entries} articoli nel fetch di verifica.\n"
            f"_Sarà attivo dal prossimo fetch delle 07:00._"
        ),
    )
    logger.info(f"Feed aggiunto: {nome} ({url}) livello {livello} id={feed_id}")


async def _handle_feeddisable(text: str) -> None:

    from src.database import get_session
    from src.models import FeedSource

    parts = text.split()
    if len(parts) < 2:
        await _send(ADMIN_ID, "⚠️ Sintassi: `/feeddisable <id>`")
        return

    try:
        feed_id = int(parts[1])
    except ValueError:
        await _send(ADMIN_ID, "⚠️ L'ID deve essere un numero intero.")
        return

    session = next(get_session())
    feed = session.get(FeedSource, feed_id)

    if not feed:
        await _send(ADMIN_ID, f"⚠️ Nessun feed trovato con id `{feed_id}`.")
        session.close()
        return

    if not feed.active:
        await _send(ADMIN_ID, f"⚠️ Il feed *{feed.name}* è già disattivato.")
        session.close()
        return

    nome = feed.name
    feed.active = False
    session.add(feed)
    session.commit()
    session.close()

    await _send(
        ADMIN_ID,
        f"🔴 Feed *{nome}* disattivato.\n_Usa `/feedenable {feed_id}` per riattivarlo._",
    )
    logger.info(f"Feed disattivato: {nome} (id={feed_id})")


async def _handle_feedenable(text: str) -> None:

    from src.database import get_session
    from src.models import FeedSource

    parts = text.split()
    if len(parts) < 2:
        await _send(ADMIN_ID, "⚠️ Sintassi: `/feedenable <id>`")
        return

    try:
        feed_id = int(parts[1])
    except ValueError:
        await _send(ADMIN_ID, "⚠️ L'ID deve essere un numero intero.")
        return

    session = next(get_session())
    feed = session.get(FeedSource, feed_id)

    if not feed:
        await _send(ADMIN_ID, f"⚠️ Nessun feed trovato con id `{feed_id}`.")
        session.close()
        return

    if feed.active:
        await _send(ADMIN_ID, f"⚠️ Il feed *{feed.name}* è già attivo.")
        session.close()
        return

    nome = feed.name
    feed.active = True
    session.add(feed)
    session.commit()
    session.close()

    await _send(
        ADMIN_ID,
        f"🟢 Feed *{nome}* riattivato.\n_Sarà incluso dal prossimo fetch delle 07:00._",
    )
    logger.info(f"Feed riattivato: {nome} (id={feed_id})")


# ── Comandi keyword ────────────────────────────────────────────


async def _handle_kwlist() -> None:
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig

    session = next(get_session())
    keywords = session.exec(
        select(KeywordConfig)
        .where(KeywordConfig.active == True)
        .order_by(KeywordConfig.cluster, KeywordConfig.weight.desc())
    ).all()
    session.close()

    if not keywords:
        await _send(ADMIN_ID, "📭 Nessuna keyword configurata.")
        return

    cluster_labels = {
        "A": "Cluster A — Territorio",
        "B": "Cluster B — Tech/Digitale",
        "C": "Cluster C — Competenze",
    }

    by_cluster: dict = defaultdict(list)
    for kw in keywords:
        by_cluster[kw.cluster].append(kw)

    lines = ["🔑 *KEYWORD ATTIVE*\n"]
    for cluster in sorted(by_cluster.keys()):
        label = cluster_labels.get(cluster, f"Cluster {cluster}")
        lines.append(f"*{label}:*")
        for kw in by_cluster[cluster]:
            lines.append(f"  • `{kw.keyword}` — peso {kw.weight}")
        lines.append("")

    lines.append("_Comandi: `/kwadd`, `/kwremove`, `/kwset`_")
    await _send(ADMIN_ID, "\n".join(lines))


async def _handle_kwadd(text: str) -> None:
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig

    parts = text.split(maxsplit=3)
    if len(parts) < 4:
        await _send(
            ADMIN_ID,
            "⚠️ Sintassi: `/kwadd <cluster> <peso> <keyword>`\n"
            "Esempio: `/kwadd B 1.5 robotica`\n"
            "Cluster validi: A, B, C",
        )
        return

    _, cluster, peso_str, keyword = parts
    cluster = cluster.upper()
    keyword = keyword.strip().lower()

    if cluster not in ("A", "B", "C"):
        await _send(ADMIN_ID, "⚠️ Cluster non valido. Usa A, B o C.")
        return

    try:
        peso = float(peso_str)
        if not (0.5 <= peso <= 3.0):
            raise ValueError
    except ValueError:
        await _send(ADMIN_ID, "⚠️ Il peso deve essere un numero tra 0.5 e 3.0.")
        return

    session = next(get_session())
    existing = session.exec(
        select(KeywordConfig).where(KeywordConfig.keyword == keyword)
    ).first()

    if existing:
        if existing.active:
            await _send(
                ADMIN_ID,
                f"⚠️ La keyword `{keyword}` esiste già nel cluster {existing.cluster} con peso {existing.weight}.",
            )
        else:
            existing.active = True
            existing.weight = peso
            existing.cluster = cluster
            session.add(existing)
            session.commit()
            await _send(
                ADMIN_ID,
                f"✅ Keyword `{keyword}` riattivata nel cluster {cluster} con peso {peso}.",
            )
        session.close()
        return

    kw = KeywordConfig(
        keyword=keyword,
        cluster=cluster,
        weight=peso,
        active=True,
    )
    session.add(kw)
    session.commit()
    session.close()

    await _send(
        ADMIN_ID,
        (
            f"✅ *Keyword aggiunta.*\n"
            f"`{keyword}` — Cluster {cluster} — peso {peso}\n"
            f"_Attiva dal prossimo fetch delle 07:00._"
        ),
    )
    logger.info(f"Keyword aggiunta: {keyword} cluster={cluster} peso={peso}")


async def _handle_kwremove(text: str) -> None:
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await _send(
            ADMIN_ID, "⚠️ Sintassi: `/kwremove <keyword>`\nEsempio: `/kwremove robotica`"
        )
        return

    keyword = parts[1].strip().lower()

    session = next(get_session())
    kw = session.exec(
        select(KeywordConfig).where(KeywordConfig.keyword == keyword)
    ).first()

    if not kw:
        await _send(ADMIN_ID, f"⚠️ Keyword `{keyword}` non trovata.")
        session.close()
        return

    cluster = kw.cluster
    peso = kw.weight
    session.delete(kw)
    session.commit()
    session.close()

    await _send(
        ADMIN_ID,
        (
            f"🗑️ *Keyword rimossa definitivamente.*\n"
            f"`{keyword}` — Cluster {cluster} — peso {peso}\n"
            f"_Disattiva dal prossimo fetch delle 07:00._"
        ),
    )
    logger.info(f"Keyword rimossa: {keyword} cluster={cluster}")


async def _handle_kwset(text: str) -> None:
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig, KeywordWeightHistory

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await _send(
            ADMIN_ID,
            "⚠️ Sintassi: `/kwset <keyword> <nuovo_peso>`\nEsempio: `/kwset robotica 2.0`",
        )
        return

    _, keyword, peso_str = parts
    keyword = keyword.strip().lower()

    try:
        nuovo_peso = float(peso_str)
        if not (0.5 <= nuovo_peso <= 3.0):
            raise ValueError
    except ValueError:
        await _send(ADMIN_ID, "⚠️ Il peso deve essere un numero tra 0.5 e 3.0.")
        return

    session = next(get_session())
    kw = session.exec(
        select(KeywordConfig)
        .where(KeywordConfig.keyword == keyword)
        .where(KeywordConfig.active == True)
    ).first()

    if not kw:
        await _send(ADMIN_ID, f"⚠️ Keyword `{keyword}` non trovata o non attiva.")
        session.close()
        return

    vecchio_peso = kw.weight
    cluster = kw.cluster  # salva prima che la sessione si chiuda

    if vecchio_peso == nuovo_peso:
        await _send(ADMIN_ID, f"⚠️ Il peso di `{keyword}` è già {nuovo_peso}.")
        session.close()
        return

    # Salva history per rollback
    history = KeywordWeightHistory(
        keyword_id=kw.id,
        keyword=kw.keyword,
        cluster=kw.cluster,
        peso_precedente=vecchio_peso,
        peso_nuovo=nuovo_peso,
        motivo="modifica_manuale",
        applicato=True,
    )
    session.add(history)

    kw.weight = nuovo_peso
    session.add(kw)
    session.commit()
    session.close()

    freccia = "⬆️" if nuovo_peso > vecchio_peso else "⬇️"
    await _send(
        ADMIN_ID,
        (
            f"{freccia} *Peso aggiornato.*\n"
            f"`{keyword}` — Cluster {cluster}: {vecchio_peso} → {nuovo_peso}\n"
            f"_Usa `/rollback` per annullare._"
        ),
    )
    logger.info(f"Keyword aggiornata: {keyword} {vecchio_peso} → {nuovo_peso}")


# ── Comandi analisi keyword ────────────────────────────────────


async def _handle_analisi() -> None:
    """Analizza keyword negli articoli approvati/scartati dell'ultima settimana."""
    global _pending_suggestions

    from sqlmodel import select

    from src.database import get_session
    from src.models import Article, KeywordConfig, PublishQueue

    session = next(get_session())
    oggi = date.today()
    una_settimana_fa = oggi - timedelta(days=7)

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

    keywords_db = session.exec(
        select(KeywordConfig).where(KeywordConfig.active == True)
    ).all()
    session.close()

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

    top_approvati = [t for t in tassi if t[4] >= 0.7 and t[1] >= 2][:5]

    top_scartati = [t for t in tassi if t[4] <= 0.3 and t[2] >= 2][:5]

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
    from sqlmodel import select

    from src.database import get_session
    from src.models import KeywordConfig, KeywordWeightHistory

    session = next(get_session())

    ultima = session.exec(
        select(KeywordWeightHistory)
        .where(KeywordWeightHistory.applicato == True)
        .order_by(KeywordWeightHistory.modificato_at.desc())
    ).first()

    if not ultima:
        await _send(ADMIN_ID, "⚠️ Nessuna modifica precedente da annullare.")
        session.close()
        return

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
