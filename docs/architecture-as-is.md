# Architettura as-is

## Contesto e obiettivo

Dritara News Monitor è un processo Python single-instance pensato per Raspberry Pi. Raccoglie RSS, deduplica e classifica articoli, chiede approvazione editoriale via Telegram, pubblica in una community e archivia export/backup su Google Drive.

## Flusso runtime

```text
APScheduler ──> fetch RSS ──> dedup batch ──> scoring ──> SQLite
     │                                                   │
     ├──> digest admin Telegram <── PublishQueue <── bot admin
     ├──> pubblicazione Telegram
     ├──> export CSV / backup DB ──> Google Drive
     └──> heartbeat

aiohttp espone GET /health nello stesso processo asyncio.
```

`main.py` avvia scheduler, health server e long polling. Lo startup ora inizializza schema e seed tramite `init_db()`.

## Componenti

| Area | File | Responsabilità attuale |
|---|---|---|
| Entrypoint | `main.py` | logging, lifecycle, avvio servizi |
| Orchestrazione | `src/scheduler.py` | pipeline giornaliera, recovery, cleanup, backup, cron |
| Admin | `src/bot.py` | polling, parsing comandi, query e mutazioni DB, analisi keyword |
| Delivery | `src/sender_telegram.py`, `src/telegram_renderer.py` | singolo adapter API Telegram, rendering HTML sicuro, coda e dedup pubblicati |
| Ingestion | `src/fetcher.py`, `src/url_security.py` | fetch concorrente bounded, DNS-pinned/peer policy e parsing RSS |
| Ranking | `src/scorer.py` | matching regex e policy editoriale |
| Persistenza | `src/database.py`, `src/models.py` | engine SQLite, seed, query ed entità |
| Export | `src/drive.py` | OAuth, CSV e backup SQLite |
| Monitoring | `src/monitor.py`, `src/healthcheck.py` | heartbeat e sola liveness |

Ogni invio Telegram attraversa `sender_telegram._send`. Il renderer tratta le stringhe legacy come testo non attendibile e consente HTML ricco solo tramite primitive che escapano i campi, rimuovono control/bidi, validano link HTTP(S) senza credenziali e non spezzano tag/entity durante lo split. `monitor.py` non possiede più un client Telegram duplicato.

`src/backup.py` e `src/sender.py` sono placeholder. `DigestFormatter` e `DigestLog` non sono integrati nel flusso principale. `config/settings.yaml` non è consumato dal codice.

## Dati e source of truth

- SQLite in `data/dritara.db` è la source of truth runtime.
- `config/feeds.yaml` e `config/keywords.yaml` inizializzano soltanto un DB vuoto.
- Gli stati principali della coda sono stringhe: `pending`, `approved`, `deferred`, `publishing`, `published`, `discarded`.
- Non esiste un sistema di migrazioni; `create_all()` non aggiorna schemi esistenti.
- Foreign key SQLite, uniqueness della coda e transizioni di stato non sono enforceate in modo completo.

## Proprietà operative

- Fetch: massimo 10 feed concorrenti e nessun retry; timeout 15 secondi per l'intera redirect chain. Il client non usa proxy ambientali, keepalive o redirect automatici; connette all'IP DNS pubblico validato e verifica il peer. Limiti: tre redirect, 2 MiB/feed in streaming, 32 MiB/run, 200 entry/feed, titolo 500, URL articolo 2048 ed excerpt 500 caratteri.
- Scheduler: timezone Europe/Rome; digest 07:00; publish 09:00, 13:00, 18:00, 22:00.
- Persistenza e Google Drive sono sincroni dentro l'unico event loop.
- Recovery startup considera eseguito il digest se trova almeno un articolo della giornata.
- `/health` risponde sempre 200 se il processo serve HTTP; non misura DB, scheduler o freschezza del digest.

## Limiti noti

I moduli bot/scheduler/sender mescolano controller, dominio, persistenza e adapter. Il job giornaliero fa commit intermedi e non registra una state machine: un errore dopo il salvataggio può lasciare una giornata parzialmente completata senza retry. Dedup fuzzy è O(n²) nel batch e non implementa realmente lo storico di sette giorni dichiarato nel README.
