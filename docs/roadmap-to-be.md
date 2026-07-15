# Product and engineering roadmap

## Regola di avanzamento

La roadmap segue il [Dritara Evidence-Gated Delivery Framework](governance/delivery-framework.md). I macro-task sono sequenziali per rischio e dipendenza; i micro-task sono piccoli e continuamente integrabili. Il macro successivo non entra in `in_progress` senza gate umano `GO`, review degli apprendimenti e documentazione aggiornata.

La manutenzione documentale `GOV.NNN` definita da ADR-004 non appartiene alla sequenza degli outcome e non può essere usata per anticipare o autorizzare un macro.

Stato corrente: **M01 `closed`** con gate umano `GO` del 2026-07-15. M02 resta `proposed` in attesa del confronto preliminare richiesto dal project owner. Registro eseguibile: [backlog](to-be/backlog.md).

## Sequenza

```text
M00 governance
 └─ M01 sicurezza/configurazione
     └─ M02 dati/migrazioni
         ├─ M03 delivery anti-duplicato
         └─ M04 digest osservabile
             └─ M05 architettura/performance
                 └─ M06 prodotto editoriale
                     └─ M07 AI assistiva
                         └─ M08 scala evidence-based
```

## M00 — Governance e baseline affidabile

- Stato: `closed`; gate `GO` del 2026-07-15.
- Outcome: repository comprensibile, misurabile e lavorabile in sicurezza da persone e agenti AI.
- Evidenze: una sessione pulita individua stato, vincoli, prossimo task e comandi; controlli documentali verdi.
- Micro-task: M00.01–M00.05.
- Macro DoD: Project Brain e baseline verificati; framework, template e checker attivi; finding collegati a task/rischi; gate review compilata; documenti riallineati; approvatore umano assegna `GO`.
- Gate: [review M00 approvata](reviews/M00-2026-07-14.md), preparata il 14 e firmata il 15 luglio 2026.

## M01 — Fondazione sicura e configurazione deterministica

- Stato: `closed`; [review M01](reviews/M01-2026-07-15.md) approvata con `GO` il 2026-07-15.
- Outcome: startup prevedibile e trust boundary esterni protetti.
- Evidenze: clean-room startup/import, negative security test, audit dipendenze e threat-model delta.
- Micro-task: M01.01–M01.05.
- Macro DoD: settings iniettati; auth e rendering uniformi; rete RSS e segreti hardened; test/failure drill verdi; runbook e threat model aggiornati; gate umano `GO`.

## M02 — Governance dati e migrazioni SQLite

- Stato: `proposed`; dipende da M01.
- Outcome: schema evolvibile senza perdita, corruzione o upgrade impliciti.
- Evidenze: fresh/legacy/production-copy upgrade, doppio upgrade no-op, restore e invarianti dati.
- Micro-task: M02.01–M02.07.
- Macro DoD: Alembic e runner governano lo schema; backup/restore provato; backfill/quarantena spiegano ogni record; readiness verifica schema head; gate umano `GO`.

## M03 — Pubblicazione exactly-once-effective

- Stato: `proposed`; dipende da M02.
- Outcome: nessun duplicato automatico; ogni invio ambiguo richiede decisione umana.
- Evidenze: concorrenza, crash injection, duplicate key e audit trail.
- Micro-task: M03.01–M03.06.
- Macro DoD: due worker producono un solo claim/call; `delivery_unknown` non viene ritentato; riconciliazione e cutover sono provati; 100% delivery ha approval/version; gate umano `GO`.

## M04 — Digest riprendibile e operazioni osservabili

- Stato: `proposed`; dipende da M02 e M03.
- Outcome: pipeline giornaliera idempotente, riprendibile e diagnosticabile.
- Evidenze: replay N volte stabile, resume dopo crash, readiness degradata correttamente e recovery da runbook.
- Micro-task: M04.01–M04.07.
- Macro DoD: run/fasi e side effect persistiti; funnel/error taxonomy/SLO visibili; I/O bloccante isolato; backup e alert operativi; gate umano `GO`.

## M05 — Monolite modulare, performance e qualità

- Stato: `proposed`; dipende dai seam stabili M02–M04.
- Outcome: codebase evolvibile da più agenti, con dipendenze controllate e capacità misurata su ARM64.
- Evidenze: fitness rule architetturali, benchmark, SBOM/audit e deploy/rollback drill.
- Micro-task: M05.01–M05.07.
- Macro DoD: domain indipendente dall'infrastruttura; god-module eliminati senza big-bang; budget CPU/RAM/latency rispettati; deploy riproducibile; gate umano `GO`.

## M06 — Prodotto editoriale utile e misurabile

- Stato: `proposed`; dipende da M03–M05.
- Outcome: l'editor seleziona rapidamente storie fresche, diverse e spiegabili, con conferma umana sempre obbligatoria.
- Evidenze: baseline/risultati UX, funnel decisionale, ranking evaluation e esperimento pre-registrato.
- Micro-task: M06.01–M06.07.
- Macro DoD: 100% decisioni tracciate, zero bypass approval e duplicate rate zero; KPI confrontati con baseline; risultato keep/change/drop; gate umano `GO`.

## M07 — AI assistiva in shadow mode

- Stato: `proposed`; dipende da M06 e da 500–1.000 label pulite/4–8 settimane di telemetria.
- Outcome: AI migliora scoperta e spiegabilità senza approvare o pubblicare.
- Evidenze: data/model card, harness offline, matched shadow evaluation, red-team e human evaluation.
- Micro-task: M07.01–M07.07.
- Macro DoD: promozione numerica e qualitativa contro baseline; nessuna regressione di coverage/costo/latency/sicurezza; fallback e kill switch; ADR umano `promote/continue-shadow/reject`.

## M08 — Evoluzione e scala guidate da evidenze

- Stato: `proposed`; dipende da baseline operative stabili.
- Outcome: cambiare infrastruttura solo quando requisiti e metriche lo giustificano.
- Evidenze: capacity/contention, bisogni prodotto, cost/failure-mode comparison e ADR.
- Micro-task: M08.01–M08.04.
- Macro DoD: trigger Postgres/cloud/multi-instance confrontati con soglie; business case, ownership, migrazione e rollback espliciti; gate umano `GO` o scelta motivata di mantenere lo stack.

## Trigger architetturali

Python, Raspberry Pi, SQLite, SQLModel, asyncio/APScheduler, Telegram e Drive restano la scelta target. Postgres, cloud multi-instance o componenti distribuiti si valutano solo con più writer/editor/tenant, HA richiesta, contesa misurata, capacity breach o backlog fuori SLA. Dettagli: [technology stack](to-be/technology-stack.md).

## Decisioni aperte da risolvere nei gate

DB storico recente, retention definitiva, RPO/RTO, SLA review, metriche audience disponibili, target di capacità Raspberry e supporto ufficiale systemd/container. Ogni decisione deve diventare task, rischio o ADR: non può restare una nota indefinita.
