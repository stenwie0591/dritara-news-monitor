# Executable micro-task backlog

Registro canonico dei micro-task. Stati: `proposed`, `ready`, `in_progress`, `in_review`, `done`, `blocked`, `cancelled`, `superseded`.

Ogni task applica la DoD globale e la propria DoD specifica. Owner ed evidenze vengono assegnati quando il task è preso in carico.

## M00 — Baseline affidabile

| ID | Stato | Outcome/deliverable | Dipendenze | DoD specifica |
|---|---|---|---|---|
| M00.01 | proposed | AS-IS verificato | nessuna | Architettura, dati, workflow e comandi riportano fonte, data e gap. |
| M00.02 | proposed | Roadmap, rischi e decisioni iniziali | M00.01 | Macro outcome, dipendenze, risk owner e approvatore sono espliciti. |
| M00.03 | proposed | Controlli e gate baseline | M00.01–02 | Comando unico e CI verdi; review compilata e decisione umana registrata. |

## Regole per prendere un task

Prima di `in_progress`: verificare Definition of Ready, owner, rischio, documenti, verifica e rollback. Lavoro emergente riceve un ID; un task `done` contiene evidenze verificabili.
