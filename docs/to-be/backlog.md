# Executable micro-task backlog

Registro canonico dei micro-task della [roadmap](../roadmap-to-be.md). Stati: `proposed`, `ready`, `in_progress`, `in_review`, `done`, `blocked`, `cancelled`, `superseded`. Ogni riga applica la [DoD globale](../governance/definition-of-done.md) **e** la DoD specifica indicata. Owner ed evidenze vengono assegnati quando il task è preso in carico.

## M00 — Governance e baseline

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M00.01 | done | Project Brain canonico | nessuna | Indice AS-IS/decisioni/TO-BE/piano completo, link locali verificati e percorso AI documentato. |
| M00.02 | done | Framework, roadmap, task/gate template | M00.01 | Ogni macro/micro ha ID, stato, dipendenze e DoD; il passaggio richiede review e firma umana. |
| M00.03 | done | Baseline tecnica e funzionale | M00.01 | Git/stack/code map/workflow/schema/test/inventario e analisi storica riportano fonte e data di verifica. |
| M00.04 | done | Governance checker e CI | M00.02 | `make check` rileva documenti/link mancanti e struttura minima; gira in CI su 3.11/3.13 senza rete/segreti. |
| M00.05 | done | Gate M00 e riallineamento documentale | M00.02–04 | Review multidisciplinare compilata, rischi e roadmap aggiornati e approvatore umano registra `GO/RECYCLE/HOLD/STOP`. |

## M01 — Sicurezza e configurazione

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M01.01 | done | Settings tipizzati e dependency injection completa | M00 | Import senza `.env`; startup aggrega errori; nessun nuovo global/load legacy; token redatti nei repr/log. |
| M01.02 | done | Autorizzazione Telegram uniforme | M01.01 | Comandi/callback accettano solo `from.id` autorizzato in chat privata; impersonation e chat non privata sono testate e negate. |
| M01.03 | done | Rendering Telegram sicuro | M01.01 | Un solo renderer effettua escaping di RSS/admin/AI, bidi/control e limiti; contract test dimostrano messaggi/link non alterabili. |
| M01.04 | done | Network policy RSS completa | M01.01 | Ogni DNS/redirect/peer IP è validato; reti private/metadata bloccate; cap, timeout, redirect ed egress target sono testati. |
| M01.05 | done | Secret e supply-chain hygiene | M01.01 | Mode file/directory verificati, token assenti dai log, dipendenze locked e nessuna vulnerabilità critica resta senza accettazione. |

## Governance maintenance

I task `GOV.NNN` seguono ADR-004: sono owner-requested, documentali e non autorizzano avanzamenti di macro.

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| GOV.001 | done | Assessment teorico e Project Brain portabile | gate M01, richiesta owner | Assessment, guida, ADR e starter kit neutro presenti; indice/stato/handoff sincronizzati; checker e `make check` verdi. |
| GOV.002 | done | Prompt brownfield autosufficiente per Codex | GOV.001, richiesta owner | Prompt copiabile copre sicurezza, inventario, M00, documenti, checker, Git, gate e brainstorming; guida/kit/checker sincronizzati e `make check` verde. |

## M02 — Dati e migrazioni SQLite

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M02.01 | in_progress | Alembic baseline e fixture legacy | M01 | Fresh upgrade, fingerprint/stamp/legacy upgrade e secondo upgrade no-op passano su fixture sintetica versionata. |
| M02.02 | proposed | Preflight e migration runner | M02.01 | Runner usa path esplicito e verifica lock, spazio, fingerprint, `quick_check` e FK; startup non migra implicitamente. |
| M02.03 | proposed | Backup e restore verificabili | M02.01 | SQLite backup API produce checksum e mode 0600; restore drill recupera DB integro entro RPO/RTO iniziali registrati. |
| M02.04 | proposed | Schema additive per run/decision/delivery | M02.01 | Tabelle, indici, FK/CHECK/UNIQUE sono additive e coperti da integration test, con downgrade/forward recovery documentato. |
| M02.05 | blocked | Backfill e quarantena legacy | M02.02–04, DB recente | Conteggi si riconciliano; JSON normalizzato; duplicati non cancellati, survivor policy e record quarantinati sono deterministici. |
| M02.06 | proposed | SQLite runtime discipline | M02.01–04 | FK per connessione, WAL, busy timeout e retry bounded attivi; readiness verifica schema head; `create_all` non effettua upgrade. |
| M02.07 | blocked | Dry-run su copia produzione | M02.02–06, snapshot recente | Upgrade/restore, invarianti, durata e spazio sono documentati; nessuna scrittura sul DB reale senza approvazione esplicita. |

## M03 — Delivery anti-duplicato

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M03.01 | proposed | Publication repository e claim atomico | M02 | Due worker ottengono un solo claim; ownership/lease e clock sono espliciti; transazioni concorrenti testate. |
| M03.02 | proposed | Shadow state machine | M03.01 | Dual-write non cambia publisher attivo; ogni mismatch legacy/nuovo è persistito, classificato e misurabile. |
| M03.03 | proposed | Delivery worker idempotente | M03.02 | Chiave lifetime articolo+destinazione, approval/version obbligatori, singola call e Telegram message ID persistito quando noto. |
| M03.04 | proposed | Crash e ambiguity handling | M03.03 | Crash prima/durante/dopo send/commit porta a stato deterministico; ambiguo è `delivery_unknown` e non genera retry automatico. |
| M03.05 | proposed | Reconciliation admin | M03.04 | Admin può confermare, autorizzare retry o annullare; callback doppio è idempotente e actor/time/reason sono auditati. |
| M03.06 | proposed | Cutover controllato | M03.02–05 | Feature flag/canary/rollback provati; recovery `publishing → approved` disabilitato; mismatch critici shadow pari a zero. |

## M04 — Digest e osservabilità

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M04.01 | proposed | DigestRun e fasi persistite | M02/M03 | Fasi hanno input/output/version/status/attempt; N rerun mantengono cardinalità e resume parte dal primo step incompleto. |
| M04.02 | proposed | Scheduler sottile | M04.01 | Scheduler registra/invoca use case senza SQL/rete/policy; misfire, timezone e doppia esecuzione hanno test deterministici. |
| M04.03 | proposed | Side-effect keys e recovery | M04.01 | Drive, notifiche e queue write sono idempotenti; retry classificati e poison/error state sono osservabili. |
| M04.04 | proposed | Funnel eventi ed error taxonomy | M04.01–03 | Raw→delivered ha correlation ID e denominatori; errori sono redatti, classificati e interrogabili. |
| M04.05 | proposed | Liveness/readiness/alert | M04.04 | Health distingue processo da capacità di servire e degrada per schema/run/backlog; alert coprono SLA, disk, backup, feed burst e unknown. |
| M04.06 | proposed | I/O off-loop, backup e retention | M04.03 | I/O sincrono non blocca event loop; timeout/retry bounded, retention e restore periodico sono esercitati. |
| M04.07 | proposed | Baseline SLI/SLO | M04.04–06 | Ogni SLI ha formula/fonte/finestra; baseline reale o proxy dichiarato e target iniziali sono approvati. |

## M05 — Architettura, performance e qualità

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M05.01 | proposed | Characterization e dependency fitness rule | M04 | Test proteggono comportamento; checker vieta dipendenze domain→framework/adapters e segnala violazioni note. |
| M05.02 | proposed | Estrazione use case | M05.01 | Digest/review/publish/recovery hanno input/output espliciti; controller restano shim senza SQL o policy. |
| M05.03 | proposed | Port, repository e adapter | M05.02 | SQL/Telegram/RSS/Drive/clock sono dietro port con contract test; transazioni sono governate dai use case. |
| M05.04 | proposed | Package layout `src/dritara` | M05.02–03 | Import/deploy aggiornati con shim per una release; suite dimostra refactor senza cambi comportamentali big-bang. |
| M05.05 | proposed | Performance pipeline | M05.02–04 | Scoring singolo, query batch, fingerprint persistente e I/O off-loop rispettano budget benchmark CPU/RAM/latency su target/proxy. |
| M05.06 | proposed | Quality engineering e supply chain | M05.01–05 | Typing/coverage risk-based, proprietà critiche, SBOM/audit e flaky rate sono misurati con soglie documentate. |
| M05.07 | proposed | Deploy ARM64 riproducibile | M05.04–06 | Install/start/stop/restart/upgrade/rollback systemd da macchina pulita passano con least privilege e log rotation. |

## M06 — Esperienza e valore editoriale

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M06.01 | proposed | Discovery e baseline UX | M04 | Job-to-be-done, pain point, tempo review/errori e ipotesi prioritarie derivano da osservazione/interviste tracciate. |
| M06.02 | proposed | Inbox versionata | M06.01 | Shortlist 6–10 e reason label; callback lega candidate-set/version e rifiuta azioni stale senza corrompere stato. |
| M06.03 | proposed | Preview modificabile e conferma | M06.02 | Flusso selezione→preview→conferma non ha bypass; esatto contenuto pubblico e attore sono memorizzati/auditati. |
| M06.04 | proposed | Ranking deterministico | M04/M06.01 | Freshness/relevance/novelty/diversity e source share sono valutati offline su candidate set versionato, scorrendo oltre top-N. |
| M06.05 | proposed | Radar territoriale editor-only | M06.02–04 | Section3 non entra nel digest; nessun fallback ne falsifica il significato; vista/sintesi resta dietro flag. |
| M06.06 | proposed | Dashboard prodotto/operativa | M04/M06.02 | Funnel, freshness, source share, review p50/p90, slot reliability e duplicati mostrano formula, fonte e finestra. |
| M06.07 | proposed | Esperimento prodotto | M06.01–06 | Ipotesi/segmento/durata/success-stop criteria sono pre-registrati; risultato porta a decisione keep/change/drop documentata. |

## M07 — AI assistiva

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M07.01 | blocked | Data readiness e governance | M06, sample minimo | Dataset card descrive lineage/retention/split temporale; label quality, leakage, PII e copyright sono revisionati. |
| M07.02 | proposed | Baseline ed evaluation harness | M07.01 | Baseline congelata; Precision@4, NDCG, recall audit, coverage, costo e latenza sono riproducibili offline. |
| M07.03 | proposed | Dedup/clustering semantico | M07.02 | Embedding/index/threshold versionati; falsi merge/split auditati; fallback deterministico provato. |
| M07.04 | proposed | Classificazione strutturata | M07.02 | Tema/territorio/value/rationale validano uno schema; output è non attendibile e il modello non dispone di action/tool. |
| M07.05 | proposed | Reranker shadow | M07.02–04 | Provider/model/prompt/policy/features versionati; matched-set vs baseline, timeout e budget senza impatto sul digest. |
| M07.06 | proposed | Human evaluation e red team | M07.05 | Campione cieco, agreement/failure taxonomy, coverage territori/fonti e prompt-injection test sono documentati. |
| M07.07 | proposed | Promotion decision | M07.05–06 | Gate numerico superato, fallback/kill switch provati e ADR umano decide promote/continue-shadow/reject senza cambiare approval. |

## M08 — Evoluzione evidence-based

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M08.01 | proposed | Capacity/contention review | baseline M04–M06 | Writer concurrency, lock wait, CPU/RAM/disk, backlog e availability sono misurati sul target. |
| M08.02 | proposed | Product scaling review | M06 | Editor, territori, tenant, canali, HA e RPO/RTO richiesti sono espliciti e validati con stakeholder. |
| M08.03 | proposed | Architecture fitness assessment | M08.01–02 | Trigger Postgres/cloud/multi-instance sono confrontati con soglie, costi, operabilità e failure mode. |
| M08.04 | proposed | Decisione evolutiva | M08.03 | ADR mantiene lo stack o approva migrazione con business case, piano incrementale, owner e rollback. |

## Regole per prendere un task

Prima di impostare `in_progress`: verificare Definition of Ready, assegnare owner, rischio, documenti impattati ed evidenze attese nel project state/handoff. Alla chiusura aggiornare stato ed evidence; lavoro emergente riceve un nuovo ID. I task high-risk seguono le estensioni risk-based della DoD.
