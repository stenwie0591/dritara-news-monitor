# Dritara News Monitor

> **EN** | [Italiano](#italiano) below
>
> An automated news monitoring system built by [Dritara](https://dritara.it) — a media brand covering tech and digital innovation in Southern Italy and Europe.

---

## English

### What is this?

Dritara News Monitor is an open-source automated pipeline that fetches, scores, and publishes tech and digital innovation news relevant to Southern Italy (Mezzogiorno) and Europe.

It runs on a Raspberry Pi, monitors 30+ RSS feeds from Italian news sources, scores articles using a keyword-based relevance engine, and delivers a daily editorial digest to a Telegram community.

### How it works

```
RSS Feeds (30+)
      ↓
  Fetcher — collects raw articles
      ↓
  Deduplicator — removes duplicates by title similarity
      ↓
  Scorer — assigns relevance score using keyword clusters:
            Cluster A (Geography: Southern Italy)
            Cluster B (Tech & Innovation)
            Cluster C (Digital Work & Talent)
      ↓
  Admin Notification — daily Telegram digest for editorial review
      ↓
  Publisher — approved articles posted to Telegram community topic
```

### Features

- **Automated fetching** of 30+ Italian RSS feeds (national and local)
- **Keyword-based scorer** with geographic and thematic clusters
- **Deduplication** across feeds and publishing history (last 7 days)
- **Editorial control** via Telegram bot commands (`/ok`, `/scarta`)
- **Daily heartbeat** with system status and feed health report
- **Scheduled publishing** at 9:00, 13:00, 18:00, 22:00
- **Deferral system** — unreviewed articles are carried over to the next day

### Tech stack

- Python 3.11+
- SQLModel + SQLite
- APScheduler
- httpx + feedparser
- python-telegram-bot
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
# Edit .env with your Telegram credentials

# Run
python main.py
```

### Configuration

| File                   | Purpose                               |
| ---------------------- | ------------------------------------- |
| `config/feeds.yaml`    | RSS feed list with source level (1–3) |
| `config/keywords.yaml` | Keyword clusters A, B, C with weights |
| `config/settings.yaml` | Thresholds, schedule, timeouts        |
| `.env`                 | Secrets (Telegram tokens, IDs)        |

### Telegram bot commands

| Command       | Description                           |
| ------------- | ------------------------------------- |
| `/ok 1 3`     | Approve articles at positions 1 and 3 |
| `/scarta 2 4` | Discard articles at positions 2 and 4 |
| `/status`     | Current queue status                  |

### Deployment (Raspberry Pi)

```bash
# Copy systemd service
sudo cp dritara.service /etc/systemd/system/
sudo systemctl enable dritara
sudo systemctl start dritara

# Check logs
tail -f logs/monitor.log
```

### Project status

Active — in daily production use by Dritara since early 2026.

---

## Italiano

### Cos'è questo progetto?

Dritara News Monitor è una pipeline automatica open-source che raccoglie, valuta e pubblica notizie su tech e innovazione digitale rilevanti per il Mezzogiorno d'Italia e l'Europa.

Gira su Raspberry Pi, monitora oltre 30 feed RSS di testate italiane, assegna uno score di rilevanza agli articoli tramite un motore keyword-based, e consegna ogni giorno una selezione editoriale a una community Telegram.

### Come funziona

```
Feed RSS (30+)
      ↓
  Fetcher — raccoglie gli articoli grezzi
      ↓
  Deduplicatore — rimuove i duplicati per similarità del titolo
      ↓
  Scorer — assegna uno score di rilevanza usando cluster di keyword:
            Cluster A (Geografia: Sud Italia)
            Cluster B (Tech & Innovazione)
            Cluster C (Lavoro Digitale & Talenti)
      ↓
  Notifica Admin — digest giornaliero Telegram per revisione editoriale
      ↓
  Publisher — articoli approvati pubblicati nel topic della community
```

### Funzionalità

- **Fetch automatico** di 30+ feed RSS italiani (nazionali e locali)
- **Scorer keyword-based** con cluster geografici e tematici
- **Deduplicazione** tra feed e storico pubblicazioni (ultimi 7 giorni)
- **Controllo editoriale** via comandi bot Telegram (`/ok`, `/scarta`)
- **Heartbeat giornaliero** con stato del sistema e salute dei feed
- **Pubblicazione schedulata** alle 9:00, 13:00, 18:00, 22:00
- **Sistema di deferral** — gli articoli non revisionati vengono riportati il giorno dopo

### Stack tecnologico

- Python 3.11+
- SQLModel + SQLite
- APScheduler
- httpx + feedparser
- python-telegram-bot
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
# Modifica .env con le tue credenziali Telegram

# Avvia
python main.py
```

### Configurazione

| File                   | Scopo                                  |
| ---------------------- | -------------------------------------- |
| `config/feeds.yaml`    | Lista feed RSS con livello fonte (1–3) |
| `config/keywords.yaml` | Cluster keyword A, B, C con pesi       |
| `config/settings.yaml` | Soglie, schedule, timeout              |
| `.env`                 | Segreti (token e ID Telegram)          |

### Comandi bot Telegram

| Comando       | Descrizione                             |
| ------------- | --------------------------------------- |
| `/ok 1 3`     | Approva gli articoli in posizione 1 e 3 |
| `/scarta 2 4` | Scarta gli articoli in posizione 2 e 4  |
| `/status`     | Stato attuale della coda                |

### Deploy (Raspberry Pi)

```bash
# Copia il service systemd
sudo cp dritara.service /etc/systemd/system/
sudo systemctl enable dritara
sudo systemctl start dritara

# Controlla i log
tail -f logs/monitor.log
```

### Stato del progetto

Attivo — in produzione quotidiana da Dritara dall'inizio del 2026.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Built with ❤️ by [Dritara](https://dritara.it) — tech and digital innovation in Southern Italy.
