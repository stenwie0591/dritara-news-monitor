# Dritara News Monitor

> **EN** | [Italiano](#italiano) below
>
> An automated news monitoring system built by [Dritara](https://dritara.it) — a media brand covering tech and digital innovation in Southern Italy and Europe.

---

## English

### What is this?

Dritara News Monitor is an open-source automated pipeline that fetches, scores, and publishes tech and digital innovation news relevant to Southern Italy (Mezzogiorno) and Europe.

It runs on a Raspberry Pi, monitors 30+ RSS feeds from Italian news sources, scores articles using a keyword-based relevance engine, and delivers a daily editorial digest to a Telegram community. Feeds and keywords are fully manageable via Telegram bot commands — no terminal access required.

### How it works

```
RSS Feeds (30+)
      ↓
  Fetcher — collects raw articles
      ↓
  Deduplicator — removes duplicates by title similarity (last 7 days)
      ↓
  Scorer — assigns relevance score using keyword clusters:
            Cluster A (Geography: Southern Italy)
            Cluster B (Tech & Innovation)
            Cluster C (Digital Work & Talent)
      ↓
  Admin Notification — daily Telegram digest split by section:
            🔴 Section 1: Sud + Tech (A+B territorial match)
            🟡 Section 2: National trends (top 5 by score)
      ↓
  Publisher — approved articles posted to Telegram community topic
      ↓
  Google Drive — daily CSV export + weekly SQLite backup
```

### Features

- **Automated fetching** of 30+ Italian RSS feeds (national and local)
- **Keyword-based scorer** with geographic and thematic clusters, territorial boost, proximity check, boilerplate blacklist
- **Deduplication** across feeds and publishing history (last 7 days)
- **Editorial control** via Telegram bot — approve, discard, defer articles
- **Fallback system** — if Section 1 is empty, best Section 2 articles with territorial match are promoted automatically
- **Max 1 article per feed** in the daily admin list to avoid source concentration
- **Feed management via bot** — add, disable, enable feeds without touching the DB
- **Keyword management via bot** — add, remove, update weights without touching the DB
- **Weekly keyword analysis** with auto-suggestions based on approval/discard history
- **Daily heartbeat** with system status, feed health report and low-yield feed alerts
- **Scheduled publishing** at 9:00, 13:00, 18:00, 22:00
- **Deferral system** — unreviewed articles carried over (max 4 times)
- **Orphan recovery** — articles stuck in `publishing` state are restored on restart
- **Weekly DB cleanup** — articles older than 90 days removed automatically
- **Google Drive integration** — daily CSV export and weekly SQLite backup

### Tech stack

- Python 3.11+
- SQLModel + SQLite
- APScheduler
- httpx + feedparser
- python-telegram-bot
- Google Drive API (oauth2)
- Deployed on Raspberry Pi (Debian 12, ARM64)

### Installation

```bash
# Clone the repo
git clone https://github.com/stenwie0591/dritara-news-monitor.git
cd dritara-news-monitor

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Telegram credentials and Google Drive folder ID
```

### Environment variables

| Variable                     | Description                    |
| ---------------------------- | ------------------------------ |
| `TELEGRAM_BOT_TOKEN`         | Bot token from @BotFather      |
| `TELEGRAM_ADMIN_CHAT_ID`     | Admin Telegram user ID         |
| `TELEGRAM_COMMUNITY_CHAT_ID` | Community group ID             |
| `TELEGRAM_NEWS_THREAD_ID`    | Topic thread ID for publishing |
| `GOOGLE_DRIVE_FOLDER_ID`     | Drive folder ID for exports    |

### Telegram bot commands

**Editorial:**

| Command       | Description                           |
| ------------- | ------------------------------------- |
| `/ok 1 3`     | Approve articles at positions 1 and 3 |
| `/scarta 2 4` | Discard articles at positions 2 and 4 |
| `/status`     | Current queue status                  |

**Keywords:**

| Command                 | Description                              |
| ----------------------- | ---------------------------------------- |
| `/kwlist`               | List all active keywords by cluster      |
| `/kwadd B 1.5 robotica` | Add keyword to cluster B with weight 1.5 |
| `/kwremove robotica`    | Remove keyword permanently               |
| `/kwset robotica 2.0`   | Update keyword weight                    |
| `/analisi`              | Weekly keyword analysis with suggestions |
| `/applica`              | Apply pending keyword suggestions        |
| `/ignora`               | Discard pending keyword suggestions      |
| `/rollback`             | Revert last keyword changes              |

**Feeds:**

| Command                         | Description                     |
| ------------------------------- | ------------------------------- |
| `/feedlist`                     | List all feeds with 7-day stats |
| `/feedadd <url> <name> <level>` | Add and validate a new RSS feed |
| `/feeddisable <id>`             | Disable a feed                  |
| `/feedenable <id>`              | Re-enable a feed                |

### Feed levels

| Level | Description                  |
| ----- | ---------------------------- |
| 1     | National tech sources        |
| 2     | Regional / thematic sources  |
| 3     | Local Southern Italy sources |

### Deployment (Raspberry Pi)

```bash
# Copy systemd service
sudo cp dritara.service /etc/systemd/system/
sudo systemctl enable dritara
sudo systemctl start dritara

# Check logs
tail -f logs/monitor.log

# Health check
curl http://localhost:8088/health
```

### Running tests

```bash
make test
```

Test suite: 146/146 ✅

### Project status

Active — in daily production use by Dritara since early 2026.

---

## Italiano

### Cos'è questo progetto?

Dritara News Monitor è una pipeline automatica open-source che raccoglie, valuta e pubblica notizie su tech e innovazione digitale rilevanti per il Mezzogiorno d'Italia e l'Europa.

Gira su Raspberry Pi, monitora oltre 30 feed RSS di testate italiane, assegna uno score di rilevanza agli articoli tramite un motore keyword-based, e consegna ogni giorno una selezione editoriale a una community Telegram. Feed e keyword sono gestibili interamente via bot Telegram — senza accesso al terminale.

### Come funziona

```
Feed RSS (30+)
      ↓
  Fetcher — raccoglie gli articoli grezzi
      ↓
  Deduplicatore — rimuove i duplicati per similarità del titolo (ultimi 7 giorni)
      ↓
  Scorer — assegna uno score di rilevanza usando cluster di keyword:
            Cluster A (Geografia: Sud Italia)
            Cluster B (Tech & Innovazione)
            Cluster C (Lavoro Digitale & Talenti)
      ↓
  Notifica Admin — digest giornaliero Telegram diviso per sezione:
            🔴 Sezione 1: Sud + Tech (match territoriale A+B)
            🟡 Sezione 2: Trend nazionali (top 5 per score)
      ↓
  Publisher — articoli approvati pubblicati nel topic della community
      ↓
  Google Drive — export CSV giornaliero + backup SQLite settimanale
```

### Funzionalità

- **Fetch automatico** di 30+ feed RSS italiani (nazionali e locali)
- **Scorer keyword-based** con cluster geografici e tematici, territorial boost, proximity check, blacklist boilerplate
- **Deduplicazione** tra feed e storico pubblicazioni (ultimi 7 giorni)
- **Controllo editoriale** via bot Telegram — approva, scarta, rimanda articoli
- **Fallback automatico** — se la Sezione 1 è vuota, i migliori articoli Sezione 2 con match territoriale vengono promossi automaticamente
- **Max 1 articolo per feed** nella lista admin giornaliera per evitare concentrazione delle fonti
- **Gestione feed via bot** — aggiunta, disattivazione, riattivazione feed senza toccare il DB
- **Gestione keyword via bot** — aggiunta, rimozione, modifica pesi senza toccare il DB
- **Analisi keyword settimanale** con suggerimenti automatici basati su storico approvazioni/scarti
- **Heartbeat giornaliero** con stato del sistema, salute dei feed e alert feed a bassa resa
- **Pubblicazione schedulata** alle 9:00, 13:00, 18:00, 22:00
- **Sistema di deferral** — gli articoli non revisionati vengono riportati (massimo 4 volte)
- **Recovery orphan** — articoli bloccati in stato `publishing` vengono ripristinati al riavvio
- **Pulizia DB settimanale** — articoli più vecchi di 90 giorni rimossi automaticamente
- **Integrazione Google Drive** — export CSV giornaliero e backup SQLite settimanale

### Stack tecnologico

- Python 3.11+
- SQLModel + SQLite
- APScheduler
- httpx + feedparser
- python-telegram-bot
- Google Drive API (oauth2)
- Deploy su Raspberry Pi (Debian 12, ARM64)

### Installazione

```bash
# Clona il repo
git clone https://github.com/stenwie0591/dritara-news-monitor.git
cd dritara-news-monitor

# Crea l'ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt

# Configura l'ambiente
cp .env.example .env
# Modifica .env con le tue credenziali Telegram e il Google Drive folder ID
```

### Variabili d'ambiente

| Variabile                    | Descrizione                            |
| ---------------------------- | -------------------------------------- |
| `TELEGRAM_BOT_TOKEN`         | Token del bot da @BotFather            |
| `TELEGRAM_ADMIN_CHAT_ID`     | ID Telegram dell'admin                 |
| `TELEGRAM_COMMUNITY_CHAT_ID` | ID del gruppo community                |
| `TELEGRAM_NEWS_THREAD_ID`    | ID del topic per la pubblicazione      |
| `GOOGLE_DRIVE_FOLDER_ID`     | ID della cartella Drive per gli export |

### Comandi bot Telegram

**Editoriali:**

| Comando       | Descrizione                             |
| ------------- | --------------------------------------- |
| `/ok 1 3`     | Approva gli articoli in posizione 1 e 3 |
| `/scarta 2 4` | Scarta gli articoli in posizione 2 e 4  |
| `/status`     | Stato attuale della coda                |

**Keyword:**

| Comando                 | Descrizione                                  |
| ----------------------- | -------------------------------------------- |
| `/kwlist`               | Lista keyword attive per cluster             |
| `/kwadd B 1.5 robotica` | Aggiunge keyword nel cluster B con peso 1.5  |
| `/kwremove robotica`    | Rimuove keyword definitivamente              |
| `/kwset robotica 2.0`   | Modifica il peso di una keyword              |
| `/analisi`              | Analisi keyword settimanale con suggerimenti |
| `/applica`              | Applica i suggerimenti keyword pendenti      |
| `/ignora`               | Scarta i suggerimenti keyword pendenti       |
| `/rollback`             | Ripristina le ultime modifiche keyword       |

**Feed:**

| Comando                           | Descrizione                         |
| --------------------------------- | ----------------------------------- |
| `/feedlist`                       | Lista feed con statistiche 7 giorni |
| `/feedadd <url> <nome> <livello>` | Aggiunge e valida un nuovo feed RSS |
| `/feeddisable <id>`               | Disattiva un feed                   |
| `/feedenable <id>`                | Riattiva un feed                    |

### Livelli feed

| Livello | Descrizione                 |
| ------- | --------------------------- |
| 1       | Fonti tech nazionali        |
| 2       | Fonti regionali / tematiche |
| 3       | Fonti locali Sud Italia     |

### Deploy (Raspberry Pi)

```bash
# Copia il service systemd
sudo cp dritara.service /etc/systemd/system/
sudo systemctl enable dritara
sudo systemctl start dritara

# Controlla i log
tail -f logs/monitor.log

# Health check
curl http://localhost:8088/health
```

### Eseguire i test

```bash
make test
```

Test suite: 146/146 ✅

### Stato del progetto

Attivo — in produzione quotidiana da Dritara dall'inizio del 2026.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Built with ❤️ by [Dritara](https://dritara.it) — tech and digital innovation in Southern Italy.
