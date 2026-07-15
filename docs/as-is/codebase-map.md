# Codebase map — AS-IS

## Runtime dependency flow

```text
main.py
 ├─ bot.py ───────────────┐
 ├─ scheduler.py          │
 │   ├─ fetcher.py ── url_security.py
 │   ├─ deduplicator.py   │
 │   ├─ scorer.py         │
 │   ├─ sender_telegram.py│
 │   ├─ monitor.py        │
 │   └─ drive.py          │
 ├─ healthcheck.py        │
 └─ database.py ── models.py

alembic.ini ── migrations/env.py ── models.py metadata
                       └─────────── schema_baseline.py (verifica legacy read-only)
```

## Ownership corrente

| Modulo | Ruolo | Problema principale | Seam target |
|---|---|---|---|
| `main.py` | composition/lifecycle | logging side-effectful | bootstrap/container |
| `bot.py` | bot, comandi, SQL, analytics | god-module ~1k LOC | controller + use case |
| `scheduler.py` | cron e intera pipeline | commit/I/O mescolati | job thin + application |
| `sender_telegram.py` | rendering, API, queue | dominio e adapter uniti | queue policy + adapter |
| `database.py` | engine, seed, query | engine globale | session factory/repository |
| `models.py` | schema SQLModel | string states, runtime ancora `create_all` | adapter DB + domain DTO |
| `migrations/`, `schema_baseline.py` | baseline Alembic e fingerprint sintetico | nessun runner/preflight runtime | migration service M02.02 |
| `fetcher.py` | ingest concorrente | config hard-coded | RSS adapter |
| `url_security.py` | safe fetch policy | peer-IP/egress residui | RSS security adapter |
| `scorer.py` | policy ranking | config e regole unite | domain policy |
| `drive.py` | export/backup | sync nell'event loop | Drive adapter/thread |
| `monitor.py` | heartbeat + SQL + Telegram | accoppiato | observability use case |
| `healthcheck.py` | liveness | sempre 200 | live/ready adapter |
| `domain/publication.py` | state machine target pura | non ancora collegata al runtime | domain seam attivo |

`formatter.py` è testato ma non integrato nel flusso principale. `backup.py` e `sender.py` sono placeholder. `DigestLog` esiste ma non è scritto; `FeedStats` è invece scritto e letto.

## Regola per nuovi file

Finché non avviene lo spostamento finale in `src/dritara/`, usare nomi espliciti e non aggiungere logica a bot/scheduler/sender. Estrarre prima funzioni pure o adapter, mantenendo shim compatibili.
