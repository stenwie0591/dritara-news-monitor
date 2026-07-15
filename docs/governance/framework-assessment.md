# Valutazione del Dritara Evidence-Gated Delivery Framework

## Scopo e conclusione

Questa valutazione conserva il riesame metodologico svolto dopo i gate M00 e M01. Il Dritara Evidence-Gated Delivery Framework è una metodologia interna coerente e riutilizzabile, ma non è uno standard autonomo o una certificazione. È un **Agile–Stage-Gate Hybrid evidence-based e risk-driven**, adattato a piccoli team e alla collaborazione tra persone e agenti AI.

La solidità teorica deriva dalla composizione esplicita di pratiche riconosciute; la validità operativa dipende invece dalla qualità delle evidenze, dalla capacità di apprendere e dall'assenza di cerimonia priva di valore. Due gate sono una baseline promettente, non una validazione definitiva: M02 e M03 dovranno verificare il metodo su migrazioni, restore, concorrenza, crash e outcome ambigui.

## Mappa teorica

| Componente Dritara | Fondamento | Applicazione locale |
|---|---|---|
| Macro-stage e gate umano | [Stage-Gate Discovery-to-Launch](https://www.stage-gate.com/about/stage-gate-innovation-performance-framework/discovery-to-launch-process/) | Outcome, deliverable/evidenze, criteri e decisione `GO/RECYCLE/HOLD/STOP` prima del macro successivo. |
| Plan–Do–Study–Act | [PDSA, Deming Institute](https://deming.org/explore/pdsa/) | Baseline e teoria, piccoli esperimenti, studio degli effetti e ripianificazione dopo gli apprendimenti. |
| Trasparenza, ispezione, adattamento e DoD | [Scrum Guide 2020](https://scrumguides.org/docs/scrumguide/v2020/2020-Scrum-Guide-US.pdf) | Stato visibile, Definition of Done condivisa e review; nessuna pretesa di applicare ruoli o cadenze Scrum completi. |
| Piccoli batch e WIP | [DORA: Working in small batches](https://dora.dev/capabilities/working-in-small-batches/) | Micro-task verificabili, WIP limitato, feedback rapido e change set piccoli. |
| Software continuamente verificabile | [DORA: Continuous delivery](https://dora.dev/capabilities/continuous-delivery/) | Test, sicurezza e documentazione durante ogni micro, non concentrati nel gate finale. |
| Memoria delle decisioni | [Architecture Decision Records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) | Record piccoli e versionati di contesto, scelta, alternative, conseguenze e supersessione. |
| Adattamento al rischio | Quality engineering e DevSecOps | Evidenze aggiuntive per dati, delivery, sicurezza, performance, operazioni e AI. |

## Il Project Brain come sistema operativo del progetto

Il Brain svolge sette funzioni coordinate:

1. memoria organizzativa versionata;
2. rappresentazione dell'AS-IS verificato;
3. pianificazione per outcome e dipendenze;
4. registro delle decisioni e dei rischi;
5. protocollo di handoff tra persone e agenti;
6. sistema di qualità e raccolta delle evidenze;
7. meccanismo di autorizzazione umana degli investimenti successivi.

La distinzione `AS-IS / DECISIONE / TO-BE / PIANO` e la gerarchia delle fonti impediscono di confondere una proposta con una funzionalità già presente. Codice e test definiscono il comportamento verificabile; `project-state.md` lo stato operativo; backlog e roadmap il lavoro futuro; ADR e gate review spiegano decisioni e autorizzazioni.

## Audit dopo M00 e M01

Valutazione interna, non certificazione:

| Dimensione | Valutazione | Evidenza o limite |
|---|---:|---|
| Coerenza teorica | 9/10 | Fonti e adattamenti dichiarati; nessuna falsa adozione di Scrum o Stage-Gate integrali. |
| Tracciabilità | 9/10 | ID, stati, backlog, ADR, handoff, review e commit collegabili. |
| Gestione del rischio | 9/10 | Risk register, DoD risk-based, rollback e controlli fail-closed. |
| Collaborazione persona–AI | 9/10 | L'agente prepara e verifica; il gate e il contenuto pubblico restano umani. |
| Automazione governance | 6/10 | CI controlla presenza, link, ID e DoD, non ancora transizioni, evidenze o staleness. |
| Misurazione valore prodotto | 5/10 | M01 era tecnico; i macro prodotto dovranno misurare outcome utente, non test count. |
| Scalabilità multi-team | 6/10 | Ottimo per un piccolo stream; mancano ownership di dominio e portfolio parallelo. |
| Maturità empirica | 4/10 | Due gate, dei quali uno solo su un macro tecnico sostanziale. |

## Punti di forza osservati

- **Separazione tra output tecnico e outcome**: un micro può essere `done` senza rendere automaticamente concluso il macro.
- **Evidenza proporzionata al rischio**: migrazione, delivery, sicurezza, performance, operazioni e AI richiedono prove diverse.
- **Human-in-the-loop reale**: l'agente non firma il proprio gate e non approva contenuti pubblici.
- **Documentazione come codice**: struttura e link entrano nella stessa feedback loop della CI.
- **Apprendimento conservato**: la review M01 registra vulnerabilità, assunzioni invalidate, portabilità e debito, non solo il risultato finale.
- **Gate non usato come code freeze**: integrazione e quality review avvengono nei micro-task.
- **Semplicità architetturale guidata da trigger**: lo stack cambia soltanto in presenza di requisiti o misure.

## Limiti e azioni di miglioramento

### Evidenze di prodotto

Nei macro prodotto le evidenze devono includere tempo, errori, adozione, qualità percepita e guardrail. Test count e copertura non misurano il valore per l'utente.

### Checker ancora strutturale

Il checker non valida ancora transizioni di stato, coerenza completa tra backlog e project state, presenza reale delle evidenze, firma dei gate o staleness dell'AS-IS. L'evoluzione consigliata è introdurre metadati machine-readable solo dopo aver stabilizzato lo schema con altri gate reali.

### Metriche di processo

Lead time, rework, CI pass rate, durata gate, document drift, change fail rate e recovery time sono dichiarati ma non ancora raccolti sistematicamente. Senza queste misure non è possibile dimostrare che il costo della governance sia inferiore al rischio e al rework evitati.

### Integrazione frequente

I commit sono piccoli, ma un branch di lunga durata può ricreare batch grandi. Nei nuovi progetti sono preferibili trunk-based development o branch di pochi giorni, feature flag e PR piccole.

### Scala organizzativa

La regola di un solo macro attivo è adatta a Dritara. Più stream indipendenti richiedono owner di dominio, limiti WIP per stream, dipendenze esplicite e un portfolio gate; non basta aumentare il WIP globale.

### Audit dell'approvazione

L'approvazione esplicita in chat è sufficiente nel contesto corrente. Progetti regolamentati devono collegare gate, identità verificata, commit o release, timestamp e firma nel sistema autorizzativo adottato.

## Criterio di validazione futura

Il framework è considerato efficace se, dopo almeno quattro macro sostanziali:

- gli incidenti e il rework attribuibili a requisiti o rischi ignorati diminuiscono;
- i micro restano completabili in ore o pochi giorni;
- i gate producono decisioni o ripianificazione, non soli verbali;
- l'AS-IS resta allineato al runtime;
- lead time e frequenza d'integrazione non peggiorano per effetto della cerimonia;
- i controlli inutili vengono rimossi e quelli nuovi hanno un failure mode concreto.

Il framework va quindi trattato come un prodotto interno: misurato, retrospettato e modificato tramite ADR.
