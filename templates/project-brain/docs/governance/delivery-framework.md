# {{PROJECT_NAME}} Evidence-Gated Delivery

## Scopo

Lifecycle leggero che combina macro-stage e gate evidence-based, PDSA, pratiche Agile/Scrum-inspired, piccoli batch e Continuous Delivery. Non dichiara l'adozione integrale di Scrum o Stage-Gate.

## Gerarchia

```text
Product Goal
└── Macro-task / outcome
    └── Micro-task / incremento verificabile
```

## Lifecycle

- macro: `proposed → ready → in_progress → gate_pending → closed`;
- micro: `proposed → ready → in_progress → in_review → done`;
- eccezioni: `blocked`, `recycle`, `hold`, `stopped`, `cancelled`, `superseded`.

Ogni macro applica Plan, Do, Study, Act. Il gate non è una fase finale di test o integrazione.

## Definition of Ready

Un macro ready esplicita outcome, non-obiettivi, baseline, evidenze, dipendenze, rischi, test, rollout/rollback, documenti e approvatore. Un micro ready aggiunge acceptance criteria e dettaglio sufficiente per non inventare requisiti.

## Regole di esecuzione

- un solo macro attivo per stream;
- WIP micro iniziale: {{WIP_LIMIT}};
- ogni change set cita un ID;
- lavoro emergente riceve un ID;
- approvazioni di gate e prodotto restano umane;
- cambi ad alto rischio richiedono test dedicati e recovery provato.

## Gate

La review confronta outcome e baseline, qualità, dati, performance, sicurezza, operazioni e processo. Esiti: `GO`, `RECYCLE`, `HOLD`, `STOP`. Un GO richiede approvatore, data, evidenze e documenti sincronizzati.

## Evoluzione

Modificare il framework tramite ADR. Aggiungere un controllo soltanto per un rischio o failure mode; rimuoverlo quando l'evidenza dimostra che è ridondante.
