# Definition of Done

## DoD globale del micro-task

Un micro-task può essere `done` solo se:

- acceptance criteria e DoD specifica sono verificati con evidenze;
- test proporzionati al rischio sono aggiunti e verdi; `make check` passa;
- sicurezza/privacy, performance, accessibilità e compatibilità sono valutate o marcate `N/A` con motivo;
- failure mode, log/metriche e comportamento operativo sono definiti;
- migrazione, feature flag e rollback sono implementati e provati quando applicabili;
- AS-IS, configurazione, runbook, backlog e ADR interessati sono aggiornati;
- nessun segreto, dato reale o output sensibile entra nel diff/log;
- review completata e handoff riporta file, test, rischi residui ed evidenze.

La checklist globale non sostituisce la DoD specifica e misurabile riportata nel backlog.

## Estensioni risk-based

| Tipo di modifica | Evidenza aggiuntiva obbligatoria |
|---|---|
| schema/dati | fixture legacy sintetica, dry-run, integrità, rollback/restore |
| queue/delivery | concorrenza, idempotenza, crash injection, ambiguous outcome |
| auth/rendering/security | test abuso, threat model, redaction e negative cases |
| scoring/editoriale | dataset versionato, metriche before/after, approval invariants |
| performance | benchmark riproducibile sul target o proxy dichiarato |
| operazioni | health/alert, runbook, install/upgrade/rollback drill |
| AI | dataset/model card, versioning, shadow evaluation, cost/latency e kill switch |

## Macro DoD

Un macro-task può ricevere `GO` solo quando:

- outcome e KPI/evidenze sono confrontati con la baseline;
- micro-task obbligatori sono `done`; differimenti hanno motivazione e nuovo ID;
- suite completa e fitness check pertinenti sono verdi;
- review di prodotto, architettura, performance, sicurezza e operazioni è conclusa;
- rischi, debito, incidenti, assunzioni invalidate e opportunità sono registrati;
- AS-IS, project state, backlog, roadmap, ADR e runbook concordano col runtime;
- il macro successivo è ripianificato alla luce degli apprendimenti;
- la gate review è firmata da un approvatore umano con esito `GO`.
