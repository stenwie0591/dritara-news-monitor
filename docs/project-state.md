# Project state

| Campo | Valore |
|---|---|
| Stato | M01 fondazione sicura/configurazione in corso |
| Macro attivo | `M01` — sicurezza e configurazione (`in_progress`) |
| Micro attivo | nessuno; `M01.05` deve ancora superare la Definition of Ready |
| WIP micro | 0 / limite predefinito 2 |
| Ultimo gate accettato | M00 `GO`, project owner, 2026-07-15 |
| Ultima verifica | 2026-07-15 |
| Baseline Git | `4eeac33`; worktree con modifiche non consolidate |
| Runtime target | Python 3.11+, Raspberry Pi ARM64, single instance |
| Verifica locale | `make check`: 220 test verdi, docs check e compileall verdi |
| DB analizzato | `data/dritara.db`, snapshot del solo 2026-03-08 |
| Fonte runtime | SQLite; YAML solo seed, salvo diversa indicazione |

## Implementato nella tranche corrente

- documentazione project brain e ADR;
- fix startup DB, JSON scoring, feedadd, keyword analysis, slot cronologici;
- permessi segreti e CSV sanitizzato;
- safe feed fetch con controllo DNS/redirect e cap;
- barriera idempotente coda e constraint per nuovi DB;
- configurazione runtime tipizzata/import-safe in corso di adozione;
- state machine pura Publication aggiunta, non ancora collegata al runtime;
- CI e dev dependencies.
- framework evidence-gated, roadmap M00–M08, 55 micro-task con DoD e template di review (M00.02 done);
- checker governance/link integrato in `make check` e CI (M00.04 done);
- gate M00 approvato dal project owner il 2026-07-15; M00 chiuso e M01 avviato.
- M01.01: validazione aggregata, logging dal composition root, settings iniettati/task-scoped in bot, scheduler, Telegram, monitor e Drive; token redatti.
- M01.02: principal Telegram verificato tramite user ID, chat configurata e chat privata, uniforme per messaggi/callback.
- M01.03: renderer HTML Telegram unico, escaping fail-safe, rimozione bidi/control, link HTTP(S) validati e splitting senza tag/entity spezzati.
- M01.04: client RSS senza proxy/retry/redirect automatici, connect DNS-pinned e peer verificato; streaming 2 MiB/feed, quota 32 MiB/run, timeout chain e field/entry limits.

## Decisioni accettate ma non ancora implementate

- approvazione con preview finale obbligatoria;
- Section3 come Radar editor-only;
- state machine digest persistita;
- delivery `delivery_unknown` senza retry automatico;
- inline buttons e reason labels;
- AI in shadow mode, mai autopublish.
- stack attuale confermato; niente microservizi/Postgres senza trigger misurati.

## Debito/blocchi

- manca il DB storico di produzione; il Drive connesso non vede i backup del Raspberry;
- DB legacy contiene duplicati di coda/pubblicazione e dati non-JSON;
- nessun framework migrazioni ancora attivo;
- recovery runtime `publishing → approved` viola la nuova decisione anti-duplicato;
- bot/scheduler/sender restano god-module;
- placeholder Docker rimossi; deploy systemd/container non ancora riproducibile;
- i messaggi legacy del bot sono ora sicuri ma inviati come testo escapato; la formattazione ricca va costruita esplicitamente con il renderer.

## Prossimi micro-task nel macro M01

1. Raffinare `M01.05` fino alla Definition of Ready: dependency lock/audit e secret hygiene finale.
2. Preparare review multidisciplinare M01 e gate umano solo dopo M01.05.

## Regola di sicurezza

Non eseguire migrazioni sul DB reale senza snapshot consistente, checksum, dry-run su copia e rollback provato.

## Regola di avanzamento

M01 è autorizzato dal gate M00. M02 non può entrare `in_progress` finché M01 non ha review completa, documentazione sincronizzata e gate umano `GO`.
