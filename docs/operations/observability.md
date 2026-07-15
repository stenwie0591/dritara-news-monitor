# Observability

M04.04–M04.07 implementa funnel, error taxonomy, health, alert e SLO; la review M04 conserva query/dashboard/drill come evidenze.

## AS-IS

Loguru stderr + file rotante; heartbeat Telegram; `/health` sempre 200; FeedStats. Mancano run ID, metriche, readiness e error state persistito.

## Target

- correlation: `run_id`, `article_id` abbreviato, `delivery_id`, phase/attempt;
- `/live`: event loop/process alive;
- `/ready`: config, DB schema head, DB write/read, scheduler, freshness ultimo run, backlog unknown;
- metriche: durata/failure fasi, funnel, freshness, precision, source share, queue state, publish latency;
- alert: digest SLA mancato, feed failure burst, delivery unknown, backup/restore fallito, disk low;
- error category strutturata e dettagli redatti.

SLO iniziali vanno misurati due settimane prima di fissare target, eccetto zero duplicati e nessun retry unknown.
