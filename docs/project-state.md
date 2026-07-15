# Project state

| Campo | Valore |
|---|---|
| Stato | M02 avviato; baseline Alembic M02.01 chiusa e M02.02 pronta |
| Macro attivo | `M02` — governance dati e migrazioni SQLite (`in_progress`) |
| Micro attivo | nessuno; `M02.02` è `ready` |
| WIP micro | 0 / limite predefinito 2 |
| Ultimo gate accettato | M01 `GO`, project owner, 2026-07-15 |
| Ultima verifica | 2026-07-15 |
| Baseline Git | branch `feature/codex_init`; `4f0a2fb` all'avvio di M02 |
| Runtime target | Python 3.11+, Raspberry Pi ARM64, single instance |
| Verifica locale | `make check`: 237 test verdi; lock installato, audit e `pip check` verdi su Python 3.13; CI run `29425476910` verde su Python 3.11/3.13 |
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
- M01.05: secret file fail-closed `0600`, log/backup directory `0700`, redazione pre-sink testata, lock runtime/dev hashati e audit CI bloccante; `python-dotenv` aggiornato a 1.2.2 per chiudere PYSEC-2026-2270.
- GOV.001: riesame teorico post M00/M01, guida di adozione, ADR-004 e starter kit neutro per esportare il Project Brain; nessun effetto su runtime o stato M02.
- GOV.002: prompt brownfield autosufficiente da copiare in un progetto esistente e affidare a Codex per migrazione documentale, bootstrap M00 e brainstorming al gate.
- M02.01: Alembic 1.18.5 senza URL predefinito, baseline fresh `0001`, fingerprint semantico legacy sintetico e 9 test fail-closed; startup e DB reale invariati.

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

## Prossimi passi

1. Avviare M02.02: preflight e migration runner con path/lock/spazio/integrità espliciti, senza database reale.
2. Preparare evidenze sintetiche per failure mode e assenza di upgrade impliciti allo startup.
3. M02.05/M02.07 restano bloccati fino a snapshot recente autorizzato.

## Prossimo micro-task ready

- ID/rischio: `M02.02` / high — `ready`; realizza il comando esplicito che precederà ogni migrazione operativa.
- Outcome: il runner usa un path assoluto, acquisisce il lock e rifiuta in modo diagnostico spazio insufficiente, fingerprint inatteso, `quick_check`/FK non validi e invocazioni concorrenti.
- Scope previsto: preflight e orchestration esplicita su database temporanei sintetici. Non-scope: startup automatico, DB reale, backfill, nuove tabelle dominio e backup/restore operativo.
- Dipendenza/evidenza attesa: M02.01 `done`; test di failure mode, doppia invocazione e prova che lo startup non migra.
- Rollback previsto: rimozione coordinata del runner; nessuna modifica a dati reali.

## Ultimo micro-task completato

- ID/owner/data: `M02.01` / Codex / 2026-07-15; stato `done`.
- Outcome/evidenze: Alembic 1.18.5 e revisione baseline su schema fresh e legacy sintetico; 9 test migration-specific, `make check` con 237 test, audit e `pip check` verdi; CI run `29425476910` verde su Python 3.11/3.13.
- Sicurezza/dati: URL SQLite esplicito e assoluto, fingerprint fail-closed e nessun URL predefinito; nessun database, backup o dato reale letto o modificato.
- Rollout/rollback: nessuna integrazione startup e nessuna migrazione operativa; rollback coordinato di scaffold, revisione e dipendenze.
- Residuo: runner/preflight, backup/restore, schema target, disciplina runtime e prova su copia produzione restano nei micro M02.02–M02.07.

## Ultima manutenzione governance

- ID/owner/data: `GOV.002` / Codex su richiesta del project owner / 2026-07-15; stato `done`.
- Outcome: prompt orchestratore dettagliato e autosufficiente per innestare il Project Brain in codebase brownfield già documentate.
- Evidenze: `templates/PROJECT_BRAIN_BOOTSTRAP_PROMPT.md`, guida/starter kit sincronizzati, checker esteso e `make check`.
- Invarianti: nessuna modifica a runtime, dati, roadmap di delivery o gate M01; M02 resta non avviato.

## Regola di sicurezza

Non eseguire migrazioni sul DB reale senza snapshot consistente, checksum, dry-run su copia e rollback provato.

## Regola di avanzamento

M01 è chiuso con gate umano `GO`; il project owner ha avviato M02 il 2026-07-15. M02.01 è `done`, M02.02 è l'unico micro `ready` e nessun altro micro M02 può iniziare finché non è concluso o esplicitamente coordinato entro il WIP.
