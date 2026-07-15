# ADR-001: monolite modulare come architettura target

- Stato: accepted
- Data: 2026-07-14
- Implementazione: partial

## Contesto

Il prodotto gira su un Raspberry Pi, ha un singolo processo, un singolo amministratore e volumi RSS limitati. I problemi osservati derivano da coupling e workflow non persistiti, non da limiti di distribuzione.

## Decisione proposta

Mantenere un singolo deploy e SQLite, separando progressivamente dominio, use case, porte e adapter. Introdurre una state machine persistita e migrazioni prima di valutare servizi separati.

## Conseguenze

Riduce il rischio operativo e permette refactoring incrementale/testabile. Non offre HA orizzontale; questa limitazione è accettabile finché non emergono requisiti multi-instance, multi-tenant o forte concorrenza.
