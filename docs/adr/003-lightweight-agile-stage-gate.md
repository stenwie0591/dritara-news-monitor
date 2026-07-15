# ADR-003: Dritara Evidence-Gated Delivery

- Stato: accepted
- Data: 2026-07-14
- Owner: product/engineering
- Implementazione: complete
- Supersedes: none

## Contesto

Il progetto viene evoluto da persone e agenti AI. Servono piccoli incrementi verificabili, memoria documentale affidabile e un controllo umano obbligatorio prima di investire nel macro-obiettivo successivo.

## Decisione

Adottare il [Dritara Evidence-Gated Delivery Framework](../governance/delivery-framework.md): macro-task outcome-oriented, micro-task in small batch, PDSA, DoD globale e specifica, review multidisciplinare e gate umano `GO/RECYCLE/HOLD/STOP`. Documentazione e ripianificazione sono parte del gate.

## Alternative

- Scrum completo: non adatto senza team/ruoli/cadenze Scrum stabili.
- Kanban senza gate: fluido, ma non rende obbligatoria la rivalutazione strategica fra macro-investimenti.
- Stage-Gate tradizionale: rischia batch grandi e test tardivi.

## Conseguenze

Maggiore tracciabilità e capacità di handoff; costo di mantenere task/evidenze. Il costo viene limitato con Markdown, automazione leggera e controlli proporzionati al rischio.

## Rollout e rollback

M00 introduce framework, template, roadmap e checker. Dopo due gate si valuta la cerimonia tramite lead time, rework e document drift. Modifiche sostanziali richiedono un ADR che sostituisca questo.

## Riesame dopo due gate — 2026-07-15

Il riesame M00/M01 conferma la decisione: tracciabilità, risk-based DoD, human gate e feedback CI hanno prodotto apprendimenti verificabili senza concentrare test e documentazione alla fine del macro. La maturità empirica resta iniziale e le metriche di processo non sono ancora raccolte sistematicamente. Assessment, criteri di validazione e limiti sono conservati in `docs/governance/framework-assessment.md`; portabilità e maintenance lane sono governate da ADR-004.
