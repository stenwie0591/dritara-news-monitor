# AI handoff protocol

## Avvio di ogni sessione

1. Leggere `AGENTS.md`, `docs/project-state.md`, il delivery framework e il documento specifico del task.
2. Eseguire `git status --short`; il worktree può contenere modifiche dell'utente o di altri agenti.
3. Verificare l'AS-IS nel codice prima di usare un TO-BE come presupposto.
4. Non leggere o stampare segreti, DB, log o contenuti editoriali salvo necessità esplicita.
5. Dichiarare file che si intende modificare per evitare collisioni tra agenti.
6. Prendere solo un micro-task `ready` del macro attivo; registrare ID, owner, rischio ed evidenze attese.

## Handoff in uscita

Riportare sempre:

- obiettivo e scope effettivo;
- file modificati;
- comportamento cambiato e invarianti preservate;
- test eseguiti e risultato;
- migrazioni/flag/rollback necessari;
- debito o rischio rimasto;
- aggiornamento richiesto a `project-state.md` e backlog.
- ID macro/micro, stato finale ed evidenze; documenti aggiornati o `N/A` motivato.

## Vincoli non negoziabili

- human approval sempre obbligatoria;
- zero retry automatici dopo invio Telegram ambiguo;
- nessuna migrazione distruttiva implicita;
- domain/application non devono acquisire nuove dipendenze da Telegram, Drive o HTTP;
- input RSS e output AI sono dati non attendibili;
- compatibilità Python 3.11 e Raspberry ARM64.

## Claim, emergent work e gate

- Evitare due agenti sullo stesso file; se emerge una collisione, fermare il write e coordinare l'ownership.
- Un requisito emerso durante il lavoro riceve un nuovo micro-task o viene registrato come rischio; non estendere silenziosamente lo scope.
- Un agente può portare un micro in `in_review`/`done` con evidenze, ma non può firmare il gate umano.
- Prima del `GO`, il reviewer usa il macro-review template, valuta gli apprendimenti e aggiorna stato, roadmap, backlog, AS-IS, rischi, ADR e runbook.

La Definition of Done completa è in [governance/definition-of-done.md](governance/definition-of-done.md).

## Ultimo handoff — M01.03

- Stato/owner/data: `M01.03` `done`, Codex, 2026-07-15.
- Scope effettivo: renderer HTML unico; adapter bot/sender/monitor centralizzato; formatter digest migrato; escaping di testo/attributi, rimozione control/bidi, link solo HTTP(S) senza credenziali e splitting conservativo entro 4096 caratteri.
- File applicativi: `src/telegram_renderer.py`, `src/sender_telegram.py`, `src/monitor.py`, `src/formatter.py`.
- Test: `tests/test_telegram_renderer.py`; `make check` verde con 211 test, docs check e compileall su Python 3.13. CI 3.11/3.13 da confermare dopo il consolidamento Git.
- Invarianti: scoring, ordine editoriale, approvazione, coda e retry invariati; nessuna migrazione o feature flag.
- Failure mode/rollback: URL non sicuro degrada a label non cliccabile; input legacy è testo escapato; errore API resta fail-closed senza retry aggiunto. Rollback applicativo tramite ripristino coordinato di renderer e adapter.
- Rischio residuo M01.03: i messaggi legacy del bot non ottengono automaticamente formattazione ricca; usare le primitive tipizzate del renderer quando la formattazione è richiesta.

## Ultimo handoff — M01.04

- Stato/owner/data: `M01.04` `done`, Codex, 2026-07-15.
- Scope effettivo: `PublicNetworkBackend` risolve IP globali e connette direttamente all'IP validato mantenendo hostname/SNI; peer obbligatorio e coincidente; client RSS senza proxy ambientali, retry, keepalive o redirect automatici; redirect rivalidati manualmente.
- Limiti: timeout 15 secondi sull'intera chain, massimo tre redirect, streaming 2 MiB/feed, quota condivisa 32 MiB/run, 200 entry/feed, titolo 500, URL articolo 2048 ed excerpt 500 caratteri.
- File applicativi: `src/url_security.py`, `src/fetcher.py`, `src/bot.py`, `requirements.txt`; test in `tests/test_url_security.py` e `tests/test_fetcher.py`.
- Evidenze: `make check` verde con 220 test, docs check e compileall su Python 3.13; test completamente offline per private/metadata IPv4/IPv6, DNS pinning, peer mismatch/mancante, redirect, cap dichiarato/reale, quota, timeout e client policy. CI 3.11/3.13 resta da confermare dopo consolidamento Git.
- Invarianti/failure: nessun retry; scoring, ordine editoriale, DB e scheduler invariati. Violazione policy fallisce il solo feed e viene registrata dall'attuale error path.
- Rollout/rollback: nessuna migrazione/flag. Rollback coordinato di factory/backend/fetch policy; non rimuovere i cap preesistenti. L'egress firewall host resta defense-in-depth del deploy M05.07, con target documentato.
- Rischio residuo: integrazione HTTPX/httpcore volutamente pin-dependent; `httpcore==1.0.9` è ora dipendenza diretta e M01.05 deve verificarne lock/audit e policy aggiornamenti.

## Ultimo handoff — M01.05

- Stato/owner/data: `M01.05` `done`, Codex, 2026-07-15. M01 non è auto-approvato: il prossimo lavoro consentito è la review macro e il gate umano.
- Scope effettivo: input dependency dichiarativi e lock runtime/dev transitivi hashati; installazione CI `--require-hashes`; audit e `pip check` bloccanti; controllo fail-closed `0600` su secret file non-symlink; writer sicuri per OAuth/log e backup `0700`/`0600`; redazione token prima dei sink.
- File principali: `requirements*.txt`, `requirements*.lock`, `Makefile`, CI, `src/secret_hygiene.py`, `main.py`, `src/drive.py`, script OAuth/backup e `tests/test_secret_hygiene.py`.
- Evidenze: clean install del lock dev riuscita in venv temporanea Python 3.13; `pip-audit` runtime senza vulnerabilità note; `pip check` verde; `make check` e clean-env suite verdi con 227 test. `python-dotenv` è passato da 1.0.1 a 1.2.2 per chiudere PYSEC-2026-2270. Matrice remota 3.11/3.13 da confermare post-push.
- Invarianti/failure: nessuna modifica a DB, stati, workflow, scoring o semantica editoriale. Un mode permissivo o symlink blocca prima della lettura; nessun segreto reale è stato letto nei test.
- Rollback/residui: nessuna migrazione/flag; rollback coordinato di bootstrap, script e lock. SBOM/update automation restano M05.06, firewall host M05.07. Prima di M02 servono review M01 e `GO` umano.
