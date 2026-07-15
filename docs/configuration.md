# Configuration registry

## Principio

Segreti e valori specifici del deploy arrivano da environment/.env; default non sensibili diventano settings tipizzati nel codice. `config/settings.yaml` è legacy/non consumato e non deve essere considerato runtime finché non viene rimosso o integrato con ADR esplicito.

| Chiave | Fonte AS-IS | Consumer | Obbligatoria | Secret | Stato |
|---|---|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | env | bot/sender/monitor | sì | sì | attiva |
| `TELEGRAM_ADMIN_CHAT_ID` | env | bot/sender | sì | identificatore sensibile | attiva |
| `TELEGRAM_ADMIN_USER_ID` | env | bot auth | sì | identificatore sensibile | attiva |
| `TELEGRAM_COMMUNITY_CHAT_ID` | env | sender | sì | identificatore sensibile | attiva |
| `TELEGRAM_NEWS_THREAD_ID` | env | sender | sì | no | attiva |
| `GOOGLE_DRIVE_FOLDER_ID` | env | drive | no | identificatore sensibile | attiva |
| `LOG_LEVEL` | env | composition root/loguru | no | no | attiva |
| `SCORE_THRESHOLD` | `.env.example` | nessuno | no | no | ignorata |
| `SECTION3_MAX_ARTICLES` | `.env.example` | nessuno | no | no | ignorata |
| `DEDUP_SIMILARITY_THRESHOLD` | `.env.example` | nessuno | no | no | ignorata |

## Costanti runtime effettive

| Area | Valore | Fonte |
|---|---|---|
| timezone | Europe/Rome | scheduler |
| digest | 07:00 | scheduler |
| publish | 09,13,18,22 | sender/scheduler |
| fetch timeout/concurrency | 15s / 10 | fetcher |
| RSS max | 2 MiB / 200 entry / 3 redirect | url security/fetcher |
| queue | max 4, deferral max 4 | sender |
| cleanup/backup | domenica 02:00/02:30 | scheduler |

## Validazione

`src/config.py` è import-safe e aggrega chiavi mancanti, token vuoto e log level invalido. `main.py` crea e valida una sola istanza, configura logging con redazione e la inietta in bot/scheduler/adapters. I fallback `get_settings()` restano per test/chiamate dirette, ma nessuna credenziale è derivata durante l'import. `SecretStr` viene convertito solo nel client provider.

## Drift legacy

`config/settings.yaml` dichiara valori diversi (backup 23:00, retry 2, log monthly) e non viene caricato. I YAML feed/keyword restano seed iniziale. Non aggiungere nuove chiavi a YAML o env senza aggiornare questa tabella e un test consumer.

## Migrazioni

`alembic.ini` non contiene `sqlalchemy.url`. Ogni invocazione richiede un URL SQLite esplicito con path assoluto, tramite `-x db_url=...` o `Config` programmatica; URL non SQLite, relativi o in-memory sono rifiutati. Questa configurazione non viene letta dallo startup applicativo.
