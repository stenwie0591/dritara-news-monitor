# Guida di adozione del Project Brain

## Quando usarlo

L'Evidence-Gated Delivery è particolarmente adatto a progetti legacy, piccoli team, sistemi con rischi operativi o di sicurezza, collaborazione con agenti AI e contesti in cui cambiano spesso esecutori o sessioni.

Non va copiato integralmente quando il costo della governance supera il rischio: prototipi usa-e-getta possono usare un profilo minimo; team numerosi e stream indipendenti richiedono un modello di portfolio; contesti regolamentati devono aggiungere controlli e firme propri.

## Nucleo metodologico portabile

Ogni istanza deve preservare questi principi:

1. distinguere AS-IS, decisioni, TO-BE e piano;
2. pianificare macro-task per outcome, non per componenti;
3. consegnare micro-task piccoli e verificabili;
4. applicare Definition of Ready e Definition of Done;
5. rendere le evidenze proporzionate al rischio;
6. integrare test, sicurezza, documentazione e operazioni durante il lavoro;
7. conservare decisioni e apprendimenti;
8. richiedere un decisore umano ai gate;
9. ripianificare il passo successivo usando ciò che si è appreso;
10. misurare e rimuovere la cerimonia che non riduce incertezza.

## Artefatti minimi

| Artefatto | Domanda a cui risponde |
|---|---|
| `AGENTS.md` | Quali regole deve rispettare qualunque esecutore? |
| `docs/README.md` | Dove si trova ogni tipo di informazione? |
| `docs/project-state.md` | Che cosa è attivo, bloccato e autorizzato adesso? |
| `docs/architecture-as-is.md` | Come funziona davvero il sistema verificato? |
| `docs/roadmap-to-be.md` | Quali outcome macro perseguiremo e in quale ordine? |
| `docs/to-be/backlog.md` | Quali micro-task sono eseguibili e quando sono done? |
| `docs/governance/delivery-framework.md` | Quali lifecycle, gate e regole di WIP usiamo? |
| `docs/governance/definition-of-done.md` | Qual è il livello minimo comune di qualità? |
| `docs/governance/risk-register.md` | Quali rischi richiedono owner, task o accettazione? |
| `docs/adr/` | Perché sono state prese le decisioni significative? |
| `docs/reviews/` | Quali evidenze e decisioni hanno chiuso i macro? |
| `docs/ai-handoff.md` | Che cosa deve sapere il prossimo esecutore? |

Threat model, runbook, data model, product metrics e documenti operativi si aggiungono quando il rischio o il dominio li rendono necessari.

## Bootstrap di un nuovo progetto

### 1. Creare il repository e copiare lo starter kit

Dal repository Dritara:

```bash
mkdir -p /percorso/nuovo-progetto
cp -R templates/project-brain/. /percorso/nuovo-progetto/
```

Lo [starter kit](../../templates/project-brain/README.md) contiene segnaposto e documenti minimi. La copia non trasferisce codice, segreti, dati, decisioni o roadmap specifiche di Dritara.

### 2. Sostituire i segnaposto

Compilare almeno `{{PROJECT_NAME}}`, `{{DATE}}`, owner, runtime, comandi standard e approvatore. Non mantenere testi Dritara se non sono veri per il nuovo progetto.

### 3. Costruire la baseline prima della roadmap

Verificare codice, test, runtime, dati e dipendenze. Scrivere l'AS-IS con fonte e data. Le lacune diventano assunzioni o rischi, non fatti inventati.

### 4. Definire il Product Goal e pochi macro-outcome

Iniziare con 3–6 macro. Ogni macro deve dichiarare utenti interessati, baseline, outcome osservabile, non-obiettivi, dipendenze, rischi, evidenze, rollout/rollback e approvatore.

### 5. Dettagliare soltanto il macro vicino

Scomporre il primo macro in micro-task di ore o pochi giorni. Il futuro lontano resta più grossolano per evitare pianificazione fittizia.

### 6. Attivare controlli automatici

Integrare nel comando unico di verifica test, compilazione/lint/type check, secret scan, dependency audit e checker dei documenti pertinenti. La CI deve essere riproducibile senza segreti o dati reali.

### 7. Eseguire un gate reale

La review deve confrontare atteso e ottenuto, registrare failure e assunzioni invalidate, sincronizzare il Brain e ottenere una decisione umana. “Tutti i task sono chiusi” non è sufficiente.

### 8. Riesaminare il framework

Dopo due o tre gate misurare lead time, rework, incidenti, drift e durata delle review. Eliminare i campi mai usati; aggiungere controlli soltanto in risposta a rischi concreti.

## Profili di rigore

| Profilo | Contesto | Applicazione |
|---|---|---|
| Lean | prototipo reversibile, nessun dato sensibile | Brain minimo, DoD essenziale, gate owner leggero. |
| Standard | prodotto piccolo/medio in esercizio | Tutti gli artefatti core, CI, risk register e gate multidisciplinare. |
| High-risk | dati critici, pagamenti, safety, regolamentazione | Segregazione ruoli, audit identity, threat model, drill, firme e compliance specifica. |

Il profilo modifica la profondità delle evidenze, non elimina la distinzione tra fatto, decisione e piano.

## Ruoli minimi

- **Owner di prodotto**: definisce outcome e accetta il rischio di investimento.
- **Owner tecnico**: garantisce fattibilità, qualità, rollout e recovery.
- **Esecutore umano o AI**: implementa e raccoglie evidenze senza auto-approvare il gate.
- **Gate approver umano**: decide `GO/RECYCLE/HOLD/STOP` e assume le azioni vincolanti.

Una persona può coprire più ruoli in un piccolo progetto, ma deve rendere esplicito quando sta cambiando responsabilità.

## Metriche da raccogliere

### Processo

- lead time e dimensione dei micro-task;
- CI pass rate e rework;
- durata ed esito dei gate;
- document drift;
- change fail rate e recovery time.

### Prodotto e operazioni

Ogni macro definisce metriche proprie, con formula, fonte, finestra, baseline e guardrail. Il numero dei test non sostituisce un outcome utente.

## Anti-pattern

- copiare il Brain senza rimuovere decisioni non vere per il nuovo progetto;
- usare il gate come grande fase finale di test o integrazione;
- dichiarare `done` con una frase generica al posto delle evidenze;
- dettagliare tutti i micro-task dell'anno prima di ottenere feedback;
- far approvare all'agente il proprio lavoro;
- trasformare metriche di processo in target individuali;
- aggiungere checklist senza rischio o failure mode;
- mantenere documenti duplicati senza una gerarchia delle fonti.

## Evoluzione e compatibilità

Ogni progetto deve trattare lo starter kit come una baseline, non come una dipendenza sincronizzata automaticamente da Dritara. Le evoluzioni locali passano da ADR; gli aggiornamenti del kit si importano confrontando principi e rischio, mai sovrascrivendo lo stato o le decisioni del progetto derivato.
