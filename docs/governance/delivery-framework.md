# Dritara Evidence-Gated Delivery Framework

## Scopo e riferimenti

Dritara usa un lifecycle interno **Evidence-Gated Delivery**, adattamento leggero dell'Agile–Stage-Gate Hybrid al lavoro di prodotto e agli agenti AI. Non dichiara di applicare Scrum o Stage-Gate integralmente: combina macro-stage e gate evidence-based, PDSA/PDCA, pratiche Scrum-inspired e Continuous Delivery.

Il modello deriva da:

- [Stage-Gate Discovery-to-Launch](https://www.stage-gate.com/about/stage-gate-innovation-performance-framework/discovery-to-launch-process/): stage di apprendimento e gate con deliverable, criteri e decisioni;
- [PDSA del Deming Institute](https://deming.org/deming-on-management-pdsa-cycle/) e [PDCA di ASQ](https://asq.org/quality-resources/pdca-cycle): pianificare, sperimentare, studiare/verificare e incorporare gli apprendimenti;
- [Scrum Guide 2020](https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-US.pdf): Definition of Done, ispezione e adattamento;
- [DORA, small batches](https://dora.dev/capabilities/working-in-small-batches/) e [Continuous Delivery](https://dora.dev/capabilities/continuous-delivery/): batch piccoli, feedback rapido, software sempre verificabile;
- [Architecture Decision Records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions): decisioni significative versionate con il codice.

## Gerarchia e fonti di verità

```text
Product Goal
└── Macro-task / Stage (outcome e gate)
    └── Micro-task (incremento verificabile)
        └── sub-task tecnico opzionale
```

| Artefatto | Responsabilità |
|---|---|
| `roadmap-to-be.md` | outcome, ordine, dipendenze e gate dei macro-task |
| `to-be/backlog.md` | registro canonico dei micro-task e loro DoD specifica |
| `project-state.md` | snapshot operativo: macro/micro attivi e ultimo gate |
| `reviews/` | evidenze e decisioni umane immutabili dei gate |
| `adr/` | decisioni architetturali significative |
| documenti AS-IS | comportamento realmente presente nel worktree verificato |
| `framework-assessment.md` | riesame teorico ed empirico del metodo |
| `adoption-guide.md` | profilo portabile e procedura di bootstrap |

Roadmap, backlog e project state non devono duplicare dettagli. In caso di conflitto, il codice/test definiscono l'AS-IS; `project-state.md` definisce lo stato operativo; il gate firmato autorizza il passaggio.

## Lifecycle

Stati macro: `proposed → ready → in_progress → gate_pending → closed`. Eccezioni: `blocked`, `recycle`, `hold`, `stopped`.

Stati micro: `proposed → ready → in_progress → in_review → done`. Eccezioni: `blocked`, `cancelled`, `superseded`.

Ogni macro applica PDSA (con la stessa logica iterativa del PDCA):

1. **Plan** — verificare AS-IS, outcome, baseline, KPI/evidenze, rischi, dipendenze, micro-task, test, rollout e rollback.
2. **Do** — consegnare micro-task piccoli, indipendenti e continuamente integrati.
3. **Study** — confrontare risultato e baseline, inclusi gli effetti inattesi; review separate di prodotto, tecnica, sicurezza/operazioni e processo.
4. **Act** — incorporare quanto appreso in codice, documenti, rischi e roadmap; sottoporre il gate umano.

Il gate non è un code freeze né il momento in cui integrare il lavoro: test, security review e documentazione avvengono durante ogni micro-task.

## Definition of Ready

Un macro-task è `ready` quando outcome, non-obiettivi, dipendenze, baseline, evidenze attese, rischi, strategia di test, rollout/rollback, documenti impattati e approvatore umano sono espliciti.

Un micro-task è `ready` quando parent macro, valore/problema, acceptance criteria, dipendenze, rischio, verifica, rollback e DoD specifica sono sufficienti perché una persona o un agente possa eseguirlo senza inventare requisiti di prodotto.

## Regole di esecuzione

- Un solo macro-task può essere `in_progress`; discovery non mutativa sul successivo è permessa, l'implementazione no.
- Il WIP micro predefinito è 2; aumentarlo richiede motivazione nel project state.
- Ogni change set cita un ID micro-task. Lavoro emergente riceve un ID prima del merge.
- Human approval resta obbligatoria per prodotto, pubblicazione e gate; un agente prepara evidenze ma non firma `GO`.
- Cambi ad alto rischio usano test dedicati, feature flag/shadow mode, migrazione expand–migrate–contract e rollback provato.
- Una scoperta che invalida outcome o sicurezza ferma il task e aggiorna rischio/backlog; non viene nascosta come dettaglio implementativo.

### Manutenzione emergente della governance

Quando nessun macro è attivo, una richiesta esplicita del project owner può ricevere un ID `GOV.NNN` se modifica soltanto metodo, documentazione, template o checker di governance. Il task deve dichiarare outcome, scope, rischio, verifica ed evidenze; non può modificare runtime, prodotto, dati o gate storici, né autorizzare il macro successivo. Qualunque cambiamento sostanziale del metodo richiede un ADR.

## Gate di fine macro-task

Prima del macro successivo si compila [il template di review](macro-review-template.md) in `docs/reviews/`. La review distingue:

1. valore prodotto e KPI;
2. architettura, dati, qualità e performance;
3. sicurezza, privacy, operabilità, migrazione e rollback;
4. retrospettiva del processo e collaborazione AI/umana;
5. aggiornamento di AS-IS, project state, backlog, roadmap, ADR, rischi e runbook.

Esiti ammessi:

- `GO`: macro DoD soddisfatta; il successivo può iniziare;
- `RECYCLE`: correzioni o evidenze mancanti; si resta sul macro corrente;
- `HOLD`: dipendenza esterna o decisione sospesa;
- `STOP`: outcome non più utile o strategia abbandonata.

Un `GO` richiede nome dell'approvatore umano, data, evidenze e documentazione sincronizzata. Il checker automatico verifica struttura e link, mai il merito o l'approvazione.

## Metriche di processo

Tracciare senza trasformarle in target individuali: lead time micro, CI pass rate, rework, durata/esito gate, document drift, change fail rate, recovery time, deployment rework e incidenti sfuggiti al gate. Le metriche prodotto e operative restano definite nella tassonomia dedicata.

## Modifica del framework

Le regole possono evolvere tramite ADR. Ridurre un controllo richiede evidenza che sia ridondante; aggiungerne uno richiede un rischio o failure mode concreto. La governance deve ridurre incertezza, non produrre cerimonia.

Il [riesame dopo M00/M01](framework-assessment.md) valuta solidità, limiti e maturità empirica. La [guida di adozione](adoption-guide.md) e lo [starter kit](../../templates/project-brain/README.md) separano i principi portabili dai contenuti specifici di Dritara.
