# Project state

| Campo | Valore |
|---|---|
| Stato | M01 chiuso; confronto preliminare richiesto prima di M02 |
| Macro attivo | nessuno; M02 autorizzato ma non avviato |
| Micro attivo | nessuno |
| WIP micro | 0 / limite predefinito 2 |
| Ultimo gate accettato | M01 `GO`, project owner, 2026-07-15 |
| Ultima verifica | 2026-07-15 |
| Baseline Git | branch `feature/codex_init`; `72b0888` prima del pacchetto gate M01 |
| Runtime target | Python 3.11+, Raspberry Pi ARM64, single instance |
| Verifica locale | `make check`: 228 test verdi; clean hash install, audit e `pip check` verdi su Python 3.13; CI run `29418776529` verde su 3.11/3.13 |
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

1. Rispondere alle domande preliminari del project owner senza avviare M02.
2. Su successiva istruzione esplicita: portare M02 `in_progress` e M02.01 `ready`.
3. M02.05/M02.07 restano bloccati fino a snapshot recente autorizzato.

## Ultimo micro-task completato

- ID/owner/data: `M01.05` / Codex / 2026-07-15; stato `done`.
- Outcome/evidenze: input e lock runtime/dev versionati; clean install `--require-hashes`; `pip-audit` senza vulnerabilità note; `pip check`; 228 test, docs e compile verdi su Python 3.13. La CI ha rilevato `greenlet` condizionale Linux, aggiunta esplicitamente, e test scorer dipendenti dalla directory DB locale, ora in-memory; run `29418456705` verde su Python 3.11/3.13.
- Sicurezza: file sensibili presenti devono essere regolari, non symlink e `0600`; token/log writer applicano `0600`, directory log/backup `0700`; contract test dimostra redazione token prima del sink.
- Rollout/rollback: nessuna migrazione/flag. File permissivo blocca startup/autorizzazione con istruzione di correggere il mode; rollback coordinato di lock, bootstrap e script.
- Residuo: SBOM e update automation restano M05.06; egress firewall host M05.07; nessun rischio critico M01.05 accettato in deroga.

## Ultima manutenzione governance

- ID/owner/data: `GOV.001` / Codex su richiesta del project owner / 2026-07-15; stato `done`.
- Outcome: valutazione metodologica conservata, limiti e criteri di validazione espliciti, guida e starter kit copiabile disponibili.
- Evidenze: ADR-004, documenti governance, asset `templates/project-brain/`, checker esteso e `make check`.
- Invarianti: nessuna modifica a runtime, dati, roadmap di delivery o gate M01; M02 resta non avviato.

## Regola di sicurezza

Non eseguire migrazioni sul DB reale senza snapshot consistente, checksum, dry-run su copia e rollback provato.

## Regola di avanzamento

M01 è chiuso con gate umano `GO`. M02 è autorizzabile, ma resta `proposed` finché il project owner non conclude il confronto preliminare e ne richiede l'avvio.
