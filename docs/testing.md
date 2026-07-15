# Strategia di test

## Quality gate corrente

`make check` esegue compilazione e suite. La CI replica questi controlli su Python 3.11 e 3.13. I test di rete reali non devono partire durante collection.

Ogni micro-task specifica le evidenze proporzionate al rischio; `done` richiede DoD globale e specifica. Il gate macro riesegue la suite completa e aggiunge i fitness check pertinenti (security, migration/restore, crash, performance, operability), senza rimandare il testing alla fine dello stage.

## Piramide target

1. Unit test puri per scoring, parsing, sanitizzazione e state transition.
2. Integration test con SQLite temporaneo per use case e idempotenza.
3. Contract test registrati/sandbox per RSS, Telegram e Drive.
4. Un end-to-end giornaliero con adapter fake e clock controllato.

## Gap prioritari

- Scheduler: run completo, run parziale, resume, doppia esecuzione e crash tra send/commit.
- Queue: claim concorrente, retry, slot passato e duplicazione.
- Security: rendering Telegram M01.03 e rete RSS M01.04 sono coperti da contract/abuse test offline; resta il drill del firewall egress sul target ARM64 in M05.07.
- Drive: CSV, backup consistente, token refresh e failure mode.
- Health/lifecycle: startup config errata, readiness e shutdown.
- Migrazioni: DB vuoto, upgrade e rollback su copia realistica.

Non usare il solo numero di test come KPI. Aggiungere coverage inizialmente informativa e alzare la soglia per moduli stabilizzati, evitando test che fissano dettagli interni durante il refactoring.

## Evidence per il gate

La macro review collega comandi/versioni, esito CI, fixture/dataset, benchmark before/after e drill. Un fallimento non viene escluso senza motivo e rischio residuo. Test manuali indicano esecutore, data e risultato; dati di produzione non entrano come fixture.
