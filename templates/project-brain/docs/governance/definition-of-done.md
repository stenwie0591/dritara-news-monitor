# Definition of Done

## DoD globale del micro-task

Un micro può essere `done` solo se:

- acceptance criteria e DoD specifica hanno evidenze;
- test proporzionati al rischio e comando di verifica sono verdi;
- sicurezza, privacy, performance, accessibilità e compatibilità sono valutate o `N/A` motivato;
- failure mode, osservabilità e comportamento operativo sono definiti;
- migrazione, feature flag e rollback sono provati quando applicabili;
- AS-IS, configurazione, runbook, backlog e ADR interessati sono aggiornati;
- nessun segreto o dato reale entra nel diff o nei log;
- review e handoff riportano file, test, rischi ed evidenze.

## Estensioni risk-based

| Tipo | Evidenza aggiuntiva |
|---|---|
| schema/dati | fixture sintetica, dry-run, integrità, backup/restore |
| queue/delivery | concorrenza, idempotenza, crash e outcome ambiguo |
| auth/security | abuse test, threat model, redaction e negative case |
| performance | benchmark riproducibile sul target o proxy dichiarato |
| operazioni | health, alert, runbook e drill upgrade/rollback |
| AI | dataset/model card, shadow evaluation, costo, latenza e kill switch |

## Macro DoD

Outcome confrontato con baseline; micro obbligatori done o differiti con nuovo ID; verifiche verdi; review multidisciplinare conclusa; rischi e documenti sincronizzati; macro successivo ripianificato; gate umano registrato.
