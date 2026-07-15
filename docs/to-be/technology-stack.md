# Technology stack decision

- Stato: decisione accettata
- Ultima verifica: 2026-07-14
- Principio: migliorare architettura e operatività prima di sostituire tecnologie adeguate.

## Stack confermato

| Tecnologia | Decisione | Condizioni |
|---|---|---|
| Python 3.11+ | mantenere | type checking e packaging progressivi |
| Raspberry Pi ARM64 | mantenere | single instance, backup off-device, hardening systemd |
| SQLite | mantenere | Alembic, FK, WAL, busy timeout, backup/restore |
| SQLModel/SQLAlchemy | mantenere | repository boundary, niente ORM nel domain |
| asyncio + APScheduler | mantenere | scheduler thin, I/O sync fuori dall'event loop |
| httpx + feedparser | mantenere | safe fetch, limiti, retry classificati |
| Telegram Bot API | mantenere | client unico, auth forte, preview e reconciliation |
| Google Drive | mantenere come adapter secondario | non source of truth; retention e restore verificati |
| scoring deterministico | mantenere come baseline/fallback | policy versionata e misurabile |

## Aggiunte approvate

- Alembic per schema versionato;
- domain state machine e application use case;
- repository/ports espliciti;
- clock iniettabile e test crash/concorrenza;
- logging strutturato e readiness;
- dependency lock con hash, audit e SBOM;
- embeddings/reranker AI dietro adapter, solo dopo data foundation.

## Tecnologie non giustificate ora

Microservizi, Kubernetes, Kafka/RabbitMQ, Postgres, async ORM, database vettoriale dedicato e framework DI. Possono essere rivalutati soltanto con evidenza di multi-instance, più editor concorrenti, HA/SLA, multi-tenancy o contesa SQLite misurata.

## Trigger di rivalutazione

- due o più processi writer necessari;
- lock/write latency oltre SLO non risolvibile con WAL/batching;
- più editor o tenant con isolamento dati;
- HA con failover automatico richiesta;
- backlog o volume che supera stabilmente la finestra batch;
- embeddings non più gestibili con indice locale/memoria.

## Giudizio

Lo stack è adeguato; l'AS-IS architetturale non lo è ancora. La roadmap deve quindi finanziare prima migrazioni, idempotenza, boundary, osservabilità e sicurezza, non una sostituzione infrastrutturale.

La scelta è riesaminata evidence-based in M08.01–M08.04; prima di allora un cambio di stack richiede un trigger misurato e un ADR, non preferenza tecnologica.
