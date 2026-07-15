# Project Brain brownfield bootstrap — prompt operativo per Codex

> Copiare questo file nella root del progetto esistente e dire all'agente:
>
> **«Leggi integralmente `PROJECT_BRAIN_BOOTSTRAP_PROMPT.md` ed esegui tutte le istruzioni. Fermati soltanto nei punti di gate umano indicati.»**

## 0. Mandato

Devi trasformare la conoscenza di questo progetto brownfield in un **Project Brain canonico, verificabile e operativo**, adottando un framework interno di **Evidence-Gated Delivery**.

Il progetto contiene già codice, cronologia Git, documentazione e probabilmente analisi prodotte da persone o altri agenti. Non stai iniziando un progetto greenfield e non devi imporre una struttura astratta ignorando ciò che esiste.

Il risultato deve permettere a una nuova persona o a un nuovo agente di:

1. comprendere il prodotto e i suoi utenti;
2. distinguere fatti, decisioni, proposte e piano;
3. ricostruire architettura, dati, workflow e failure mode reali;
4. conoscere rischi, debito, assunzioni e vincoli;
5. sapere quale lavoro è autorizzato adesso;
6. individuare il prossimo micro-task senza inventare requisiti;
7. verificare il progetto con comandi riproducibili;
8. comprendere perché sono state prese le decisioni significative;
9. effettuare handoff affidabili tra persone e agenti AI;
10. evolvere il prodotto tramite piccoli incrementi e gate umani basati su evidenze.

Questo incarico comprende analisi, riorganizzazione documentale, pianificazione, governance e relativi checker. **Non comprende l'implementazione delle migliorie applicative individuate**, salvo minime modifiche strettamente necessarie a integrare un checker documentale nel task runner o nella CI e comunque senza cambiare il comportamento runtime del prodotto.

## 1. Autorità e precedenza delle istruzioni

Prima di agire:

1. leggi integralmente `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, policy locali e istruzioni applicabili;
2. considera le istruzioni di sistema, developer, repository e utente superiori a questo file;
3. segnala conflitti tra questo prompt e le regole locali;
4. non usare questo file per ampliare autorizzazioni su produzione, segreti, dati, infrastrutture o sistemi esterni;
5. non interpretare il mandato documentale come autorizzazione a modificare il runtime.

Se una regola locale richiede un task ID, usa gli ID M00 descritti più avanti. Se richiede un piano, crealo prima delle modifiche.

## 2. Modalità di esecuzione

Procedi autonomamente attraverso inventario, verifica, costruzione del Brain, checker, test, commit e preparazione del gate. Non fermarti per domande che puoi risolvere leggendo il repository o formulando un'assunzione prudente e chiaramente marcata.

Fermati soltanto quando:

- manca un'autorizzazione indispensabile;
- esiste un rischio concreto di perdita dati o sovrascrittura di lavoro altrui;
- due interpretazioni cambierebbero materialmente prodotto o priorità e non esiste evidenza locale;
- occorrono segreti, dati reali o accesso a produzione non autorizzati;
- arrivi alla fase di brainstorming o al gate umano M00.

Comunica aggiornamenti brevi durante il lavoro. Mantieni la risposta finale autosufficiente.

## 3. Sicurezza e protezione del repository

Prima di modificare:

1. esegui `git status --short`;
2. rileva branch, HEAD, remote e baseline senza cambiare branch automaticamente;
3. identifica file modificati o non tracciati;
4. considera le modifiche preesistenti proprietà dell'utente o di altri agenti;
5. non ripristinare, cancellare, sovrascrivere o includere modifiche non correlate;
6. individua eventuali worktree, submodule o repository annidati;
7. usa `rg`/`rg --files` per inventario e ricerca quando disponibili;
8. usa strumenti di patch sicuri per le modifiche testuali;
9. evita comandi distruttivi e operazioni Git che riscrivono la storia;
10. non lavorare direttamente su `main`, `master` o branch protetti.

Non leggere, stampare, copiare, indicizzare o committare, salvo autorizzazione esplicita e necessità dimostrata:

- `.env` e varianti locali;
- chiavi private, token, cookie o credential store;
- file OAuth o cloud credentials;
- database reali e relativi WAL/journal;
- backup;
- log runtime;
- export di produzione;
- dati personali, editoriali o commerciali non necessari;
- artefatti che possono contenere segreti.

Puoi ispezionare nomi di file, schema dichiarativo, fixture sintetiche, migrazioni versionate e configurazioni di esempio prive di segreti.

Se trovi un possibile segreto nel repository:

1. non stamparne il valore;
2. registra soltanto tipo, percorso e rischio in forma redatta;
3. evita di aggiungerlo al diff;
4. raccomanda rotazione o rimozione senza eseguirla se non autorizzato.

## 4. Principio epistemico del Brain

Classifica ogni informazione importante in una delle categorie seguenti.

### AS-IS

Comportamento o stato verificato nel codice, nei test, nelle migrazioni, nella configurazione dichiarativa o nel runtime analizzabile in sicurezza. Ogni claim importante deve indicare fonte e data di verifica.

### DECISIONE

Scelta esplicitamente accettata da un owner autorizzato. Può essere non ancora implementata. Deve essere distinguibile da una raccomandazione dell'agente.

### TO-BE

Design target, proposta o ipotesi di evoluzione. Non è prova di implementazione e non diventa decisione senza il processo previsto.

### PIANO

Sequenza di lavoro con outcome, dipendenze, acceptance criteria, evidenze e rollback.

### ASSUNZIONE

Affermazione plausibile ma non verificata. Deve avere un metodo di verifica, un owner o un rischio associato.

### STORICO

Informazione utile a comprendere il passato ma non più autorevole sul comportamento o sul piano corrente.

### CONTRADDIZIONE

Due fonti incompatibili che non possono essere risolte con le evidenze disponibili. Registrala esplicitamente; non scegliere silenziosamente la versione più conveniente.

Gerarchia predefinita delle fonti:

1. codice e test descrivono il comportamento tecnicamente verificabile;
2. runtime e dati descrivono lo stato operativo solo quando ispezionati in sicurezza;
3. `project-state.md` descrive lavoro attivo, blocchi e ultimo gate;
4. ADR e gate review descrivono decisioni accettate;
5. roadmap e backlog descrivono il futuro;
6. documenti legacy forniscono contesto, non prevalenza automatica;
7. il codice non determina da solo l'intento di prodotto;
8. una raccomandazione AI non è una decisione;
9. un test verde dimostra soltanto ciò che il test misura;
10. assenza di evidenza non equivale a evidenza di assenza.

## 5. Framework da adottare

Implementa un lifecycle interno **Evidence-Gated Delivery**, adattamento leggero di:

- Agile e Lean per feedback e piccoli batch;
- Stage-Gate per decisioni di investimento tra macro-outcome;
- PDSA/PDCA per apprendimento empirico;
- Scrum-inspired Definition of Done, ispezione e adattamento;
- Continuous Integration/Delivery per software continuamente verificabile;
- risk-based quality engineering e DevSecOps;
- Architecture Decision Records per memoria delle decisioni;
- human-in-the-loop per prodotto, rischio e approvazioni non delegabili.

Non dichiarare l'adozione integrale di Scrum, Stage-Gate, ITIL o altri standard se ruoli, eventi e accountability non sono realmente applicati.

Gerarchia:

```text
Product Goal
└── Macro-task / Stage: outcome e gate
    └── Micro-task: incremento verificabile
        └── Sub-task tecnico opzionale
```

Stati macro:

```text
proposed → ready → in_progress → gate_pending → closed
```

Eccezioni macro:

```text
blocked | recycle | hold | stopped
```

Stati micro:

```text
proposed → ready → in_progress → in_review → done
```

Eccezioni micro:

```text
blocked | cancelled | superseded
```

Regole iniziali:

- un solo macro `in_progress` per stream di delivery;
- WIP micro predefinito 2, salvo motivazione;
- ogni change set cita un task ID;
- lavoro emergente riceve un ID prima del merge;
- un agente può preparare evidenze ma non firmare un gate umano;
- test, documentazione, sicurezza e operazioni avvengono durante i micro-task;
- il gate non è una fase finale di integrazione;
- una scoperta che invalida outcome o sicurezza aggiorna rischio e piano;
- i controlli nuovi devono rispondere a un rischio o failure mode concreto;
- le regole del framework evolvono tramite ADR.

Ogni macro segue PDSA:

1. **Plan**: baseline, outcome, non-obiettivi, teoria, KPI/evidenze, rischi, dipendenze, test, rollout e rollback;
2. **Do**: piccoli incrementi continuamente integrabili;
3. **Study**: confronto atteso/ottenuto, inclusi effetti inattesi e assunzioni invalidate;
4. **Act**: incorporazione degli apprendimenti in documenti, rischi e roadmap, quindi gate umano.

Esiti gate:

- `GO`: outcome ed evidenze sufficienti; il macro successivo può iniziare;
- `RECYCLE`: servono correzioni o evidenze aggiuntive;
- `HOLD`: dipendenza o decisione esterna sospende il lavoro;
- `STOP`: outcome o strategia sono abbandonati.

## 6. Macro di bootstrap obbligatorio

Crea il macro:

### M00 — Governance, baseline e Project Brain affidabile

Outcome:

> Una nuova persona o un nuovo agente può comprendere stato, prodotto, architettura, dati, rischi, decisioni, comandi, priorità e prossimo lavoro senza inventare fatti o requisiti.

M00 non modifica intenzionalmente il comportamento runtime.

### M00.01 — Inventario e migrazione documentale

- Outcome: tutta la conoscenza preesistente ha una destinazione e uno stato espliciti.
- Rischio: perdita o deformazione della conoscenza storica.
- Evidenze: inventario, migration map, link e diff.
- DoD specifica:
  - tutti i documenti sono censiti;
  - ciascuno è classificato come canonico, da verificare, storico, duplicato o superseded;
  - il contenuto utile ha una destinazione;
  - contraddizioni e lacune sono registrate;
  - nessuna eliminazione silenziosa.

### M00.02 — Baseline tecnica, funzionale e operativa

- Outcome: l'AS-IS è verificato contro fonti primarie del repository.
- Rischio: trasformare documentazione o output AI in fatti non verificati.
- Evidenze: file/linee, test, comandi, schema dichiarativo e data di verifica.
- DoD specifica:
  - codebase, stack, feature, workflow, dati, contratti, configurazione, test e operazioni sono mappati;
  - AS-IS, decisioni e TO-BE sono separati;
  - confidence e gap sono espliciti;
  - nessun segreto o dato reale è stato acquisito.

### M00.03 — Strategia, rischi, architettura target e backlog

- Outcome: i finding diventano decisioni proposte, rischi o lavoro eseguibile.
- Rischio: roadmap technology-driven o over-engineered.
- Evidenze: Product Goal, risk register, ADR, roadmap, dipendenze e DoD.
- DoD specifica:
  - ogni macro ha outcome, baseline, evidenze, dipendenze e Macro DoD;
  - ogni micro ha ID, stato, dipendenze e DoD specifica;
  - ogni finding importante è collegato a rischio, task, ADR o accettazione;
  - il TO-BE preserva ciò che funziona e indica rollout/rollback.

### M00.04 — Governance checker e CI

- Outcome: il Brain non dipende soltanto dalla disciplina manuale.
- Rischio: document drift o governance non applicata.
- Evidenze: checker offline, test e run CI.
- DoD specifica:
  - documenti core e link locali sono verificati;
  - ID duplicati/orfani e macro senza DoD sono rilevati;
  - il checker entra nel comando standard e nella CI esistente;
  - il controllo non legge rete, segreti, DB o log;
  - gli errori sono comprensibili e azionabili.

### M00.05 — Review multidisciplinare e gate

- Outcome: baseline e piano vengono sottoposti a decisione umana.
- Evidenze: review M00, test verdi, documentazione sincronizzata.
- DoD specifica:
  - review di prodotto, architettura, dati, qualità, performance, sicurezza, privacy, operazioni e processo completata;
  - apprendimenti, assunzioni invalidate, debito e rischi registrati;
  - prossimo macro ripianificato;
  - approvatore e decisione lasciati `pending` fino all'intervento umano.

## 7. Inventario brownfield

Prima di creare la nuova struttura:

1. elenca documenti, codice, test, configurazioni dichiarative, workflow CI e script operativi;
2. identifica convenzioni esistenti e fonti ritenute autorevoli;
3. individua analisi precedenti di Claude, Codex o altri agenti;
4. separa osservazioni verificabili da raccomandazioni;
5. rileva documenti duplicati o con finalità sovrapposte;
6. cerca riferimenti a file che potrebbero essere spostati;
7. registra data, commit e ambiente della baseline;
8. non leggere file sensibili per “completezza”.

Crea una migration map con almeno:

| Fonte attuale | Tipo/contenuto | Stato | Evidenza/confidenza | Destinazione Brain | Azione |
|---|---|---|---|---|---|
| percorso | setup/architettura/requisito/... | canonico/legacy/... | alta/media/bassa | nuovo percorso | merge/riscrivi/archivia/mantieni |

Regole di migrazione:

- non cancellare finché contenuto e link non sono riconciliati;
- preferisci mantenere temporaneamente un documento con banner `superseded` piuttosto che spezzare riferimenti;
- sposta in `docs/legacy/` solo quando migliora realmente la navigazione;
- preserva attribuzione, decisioni e razionale;
- non copiare errori noti nel nuovo AS-IS;
- non mantenere due fonti canoniche sullo stesso stato;
- usa Git per la storia, ma non come giustificazione per perdere contesto leggibile.

## 8. Analisi AS-IS obbligatoria

Analizza in profondità, nella misura pertinente al progetto:

### Prodotto e utenti

- problema risolto;
- utenti, operatori e stakeholder;
- user journey e job-to-be-done osservabili;
- funzionalità dichiarate e realmente implementate;
- invarianti di prodotto;
- metriche e feedback disponibili;
- comportamenti non documentati;
- funzionalità incomplete o inutilizzate.

### Repository e build

- linguaggi e versioni;
- package/dependency manager;
- entrypoint;
- build, test e task runner;
- layout e package boundaries;
- artifact e release process;
- ambienti supportati;
- dipendenze dirette/transitive e lock;
- compatibilità target.

### Architettura

- componenti e responsabilità;
- composition root;
- dipendenze tra layer;
- domain, application, infrastructure e adapter;
- global state e service locator;
- coupling e cicli;
- god module;
- boundary interni ed esterni;
- scelte deliberate rispetto ad accidental architecture.

### Dati

- source of truth;
- modelli e schema;
- lifecycle e ownership;
- migrazioni;
- constraint, indici e integrità;
- transazioni e concorrenza;
- retention;
- backup e restore;
- PII o dati sensibili;
- legacy e compatibilità;
- rischio di perdita, duplicazione o corruzione.

Non aprire database reali senza autorizzazione. Usa modelli, migrazioni, fixture sintetiche e test.

### Workflow e stato

- flussi sincroni, asincroni, batch e schedulati;
- state machine implicite o esplicite;
- transizioni e invarianti;
- idempotenza;
- retry, timeout e backoff;
- concorrenza e claim;
- crash prima/durante/dopo side effect;
- outcome ambiguo;
- recovery e riconciliazione;
- orologi, timezone e ordering.

### Contratti esterni

- API, webhook, code, storage e provider;
- autenticazione e autorizzazione;
- timeout e retry;
- rate limit;
- schema/versioning;
- dati non attendibili;
- redirect, SSRF e network boundary;
- idempotency key;
- circuit breaker o degradation;
- contract test e fake.

### Configurazione e segreti

- fonti di configurazione;
- precedenza e validazione;
- import-time side effect;
- settings tipizzati;
- dependency injection;
- secret storage;
- redaction;
- file mode e least privilege;
- environment drift;
- configurazioni non più usate.

### Sicurezza e privacy

- asset, attori e trust boundary;
- autenticazione e autorizzazione;
- input validation e output encoding;
- injection;
- path traversal;
- SSRF;
- deserializzazione;
- supply chain;
- logging sensibile;
- abuse case;
- privacy, retention e minimizzazione;
- threat e mitigazioni esistenti.

### Qualità e test

- piramide dei test reale;
- unit, integration, contract ed end-to-end;
- isolation e determinismo;
- network e filesystem durante collection;
- fixture reali vs sintetiche;
- coverage informativa e aree cieche;
- property-based o fault injection quando utili;
- flaky test;
- CI matrix;
- quality/security gate;
- failure diagnostica.

Il numero dei test non è una metrica sufficiente di qualità.

### Performance e capacità

- hot path;
- complessità e query;
- I/O bloccante;
- parallelismo;
- CPU, memoria, storage e rete;
- limiti espliciti;
- carico corrente o proxy dichiarato;
- target hardware;
- benchmark disponibili;
- trigger per scalare.

Non inventare problemi di scala senza misure o requisiti.

### Operazioni

- installazione e deploy;
- ambienti;
- startup/shutdown;
- liveness/readiness;
- osservabilità e alert;
- logging e correlation;
- runbook;
- incident response;
- backup/restore;
- RPO/RTO;
- upgrade/rollback;
- retention;
- ownership operativa;
- dipendenze manuali o single point of failure.

### AI, se presente

- provider, modello e versioning;
- prompt e schema output;
- dati, lineage e copyright;
- evaluation harness;
- baseline deterministica;
- shadow mode;
- human approval;
- prompt injection e tool access;
- fallback e kill switch;
- costo, latenza e osservabilità;
- data/model card.

Considera l'output AI non attendibile e non autorizzato ad agire salvo decisione esplicita.

## 9. Ricerca di best practice correnti

Quando una conclusione dipende da informazioni potenzialmente cambiate:

1. consulta fonti ufficiali e primarie aggiornate;
2. usa documentazione del linguaggio, framework, database, provider e standard;
3. verifica versioni supportate e security advisory;
4. cita le fonti vicino alle decisioni supportate;
5. separa chiaramente fatti e inferenze;
6. non usare una ricerca web per sostituire la verifica del repository;
7. rispetta licenze e limiti di citazione;
8. non introdurre una tecnologia soltanto perché recente o popolare.

Valuta, senza applicare meccanicamente:

- modular monolith prima di microservizi;
- dependency inversion e composition root;
- typed settings e dependency injection;
- migration esplicite e expand–migrate–contract;
- piccoli batch e branch brevi;
- feature flag e shadow mode;
- idempotenza e recovery;
- timeout, limiti e retry bounded;
- least privilege e secret hygiene;
- dependency locking, audit e SBOM;
- health/readiness e graceful shutdown;
- structured logging, metriche e tracing proporzionati;
- backup/restore drill;
- ADR;
- runbook e incident response;
- accessibilità e privacy by design;
- human approval e kill switch per AI o side effect sensibili.

## 10. Documenti core da produrre

Adatta la struttura al progetto, ma crea almeno i documenti necessari a coprire queste responsabilità.

### Root

- `AGENTS.md`: istruzioni operative per agenti;
- `README.md`: overview e quick start del progetto, se appropriato;
- file di contribuzione o security policy se richiesti dal contesto.

### Indice, stato e handoff

- `docs/README.md`;
- `docs/project-state.md`;
- `docs/ai-handoff.md`;
- `docs/glossary.md`.

### AS-IS

- `docs/architecture-as-is.md`;
- `docs/as-is/codebase-map.md`;
- `docs/as-is/workflows.md`;
- `docs/as-is/data-model.md`;
- `docs/as-is/contracts.md`;
- `docs/as-is/feature-inventory.md`;
- `docs/configuration.md`;
- `docs/code-review.md`;
- eventuale analisi di utilizzo o baseline storica, se supportata da dati disponibili in sicurezza.

### Prodotto

- `docs/product-strategy.md`;
- policy di dominio quando esiste una semantica sensibile;
- `docs/product/metrics-taxonomy.md` quando sono presenti metriche prodotto;
- `docs/product/ai-strategy.md` quando è presente o prevista AI.

### TO-BE e piano

- `docs/to-be/target-architecture.md`;
- `docs/to-be/technology-stack.md`;
- `docs/to-be/state-machines.md` quando applicabile;
- `docs/to-be/migration-plan.md`;
- `docs/to-be/backlog.md`;
- `docs/roadmap-to-be.md`.

### Governance

- `docs/governance/delivery-framework.md`;
- `docs/governance/definition-of-done.md`;
- `docs/governance/risk-register.md`;
- `docs/governance/adr-index.md`;
- `docs/governance/adr-template.md`;
- `docs/governance/macro-task-template.md`;
- `docs/governance/micro-task-template.md`;
- `docs/governance/macro-review-template.md`.

### Decisioni e gate

- `docs/adr/` con ADR iniziali proposte o accettate solo quando autorizzate;
- `docs/reviews/README.md`;
- `docs/reviews/M00-YYYY-MM-DD.md` con decisione `PENDING`.

### Sicurezza, qualità e operazioni

- `docs/security/threat-model.md`;
- `docs/testing.md`;
- `docs/runbook.md`;
- `docs/operations/deployment.md`;
- `docs/operations/observability.md`;
- `docs/operations/backup-restore.md`.

Quando pertinente aggiungi privacy, compliance, API, accessibility, performance, disaster recovery o incident response.

Non creare file vuoti per soddisfare una lista. Un argomento semplice può essere una sezione `N/A` motivata nel documento più vicino. Crea un documento separato quando ha lifecycle, ownership, rischio o pubblico propri.

## 11. Contenuto minimo dei documenti principali

### `docs/README.md`

Deve:

- dichiarare la data e la baseline;
- spiegare AS-IS, DECISIONE, TO-BE, PIANO, ASSUNZIONE e STORICO;
- fornire un percorso minimo di lettura;
- catalogare i documenti per responsabilità;
- distinguere canonico, legacy e superseded;
- definire la gerarchia delle fonti;
- impedire che il TO-BE venga letto come implementato.

### `docs/project-state.md`

Deve essere breve e operativo. Includi:

- stato complessivo;
- macro e micro attivi;
- WIP;
- ultimo gate;
- data e baseline Git;
- runtime target;
- comando standard di verifica;
- implementato nella tranche corrente;
- decisioni accettate non implementate;
- debito e blocchi;
- prossimi passi;
- ultimo task completato;
- regola di sicurezza;
- regola di avanzamento.

### `docs/ai-handoff.md`

Definisci:

- bootstrap di sessione;
- protezione di segreti e worktree;
- claim/ownership dei task;
- vincoli non negoziabili;
- protocollo per lavoro emergente;
- handoff in uscita;
- ultimo task con file, comportamento, invarianti, test, rollback e rischio residuo;
- ultimo gate.

### `docs/code-review.md`

Organizza i finding per severità e area. Ogni finding deve avere:

- evidenza;
- impatto;
- stato;
- mitigazione;
- task/rischio/ADR associato;
- eventuale motivo di accettazione.

### `docs/governance/definition-of-done.md`

La DoD globale del micro deve coprire:

- acceptance criteria ed evidenze;
- test e comando standard verdi;
- sicurezza e privacy;
- performance;
- accessibilità;
- compatibilità;
- failure mode;
- log/metriche e operabilità;
- migrazione;
- feature flag;
- rollout/rollback;
- documentazione e ADR;
- segreti e dati reali;
- review e handoff.

Aggiungi estensioni risk-based per:

- schema/dati;
- queue/delivery;
- auth/rendering/security;
- ranking/scoring/logica di business;
- performance;
- operazioni;
- AI.

Definisci anche la Macro DoD.

## 12. Strategia TO-BE

La proposta target deve:

1. derivare da outcome, rischio o failure mode verificati;
2. preservare il comportamento utile;
3. dichiarare non-obiettivi;
4. evitare riscritture big-bang;
5. preferire seam, shim, strangler, feature flag e migrazioni additive;
6. separare domain/application dagli adapter esterni quando utile;
7. mantenere lo stack semplice finché metriche o requisiti non giustificano altro;
8. definire trigger quantitativi per database, cloud, distribuzione o scala;
9. includere compatibilità, rollout, rollback e recovery;
10. distinguere chiaramente decisioni accettate da ADR proposte;
11. indicare costi e conseguenze negative;
12. non promettere benefici non misurabili.

Per ogni proposta significativa confronta almeno:

- mantenere e correggere;
- refactoring incrementale;
- sostituzione;
- non fare nulla per ora.

## 13. Roadmap e backlog

Ordina i macro principalmente per rischio, dipendenze e valore. Una sequenza iniziale tipica, da adattare, è:

1. governance e baseline;
2. sicurezza/configurazione;
3. dati e migrazioni;
4. idempotenza/delivery;
5. workflow e osservabilità;
6. architettura/performance;
7. esperienza e outcome prodotto;
8. AI assistiva;
9. scala guidata da evidenze.

Non usare questo ordine se il progetto dimostra priorità diverse. Documenta la motivazione.

Ogni macro deve includere:

- ID e stato;
- owner e approvatore umano;
- outcome e utenti interessati;
- baseline/problema;
- KPI o evidenze target;
- scope e non-obiettivi;
- dipendenze e rischi;
- micro obbligatori;
- piano test;
- rollout/rollback;
- documenti impattati;
- gate previsto;
- Macro DoD.

Ogni micro deve includere:

- ID e parent;
- stato e owner;
- outcome osservabile;
- scope/non-scope;
- dipendenze;
- rischio e motivazione;
- acceptance criteria Given/When/Then o metriche;
- verifica;
- rollout/rollback o `N/A` motivato;
- documenti impattati;
- evidenze `pending` finché non concluse;
- DoD specifica misurabile.

I micro devono essere piccoli: ore o pochi giorni. Se superano circa una settimana, prova a dividerli per seam, rischio, percorso o evidenza.

Un finding importante deve diventare almeno uno tra:

- rischio;
- micro-task;
- ADR proposta;
- debito esplicitamente accettato;
- assunzione con piano di verifica.

## 14. Risk register

Ogni rischio contiene:

- ID;
- descrizione concreta;
- probabilità e impatto;
- asset/outcome coinvolto;
- trigger osservabile;
- mitigazione;
- owner;
- task associato;
- stato;
- eventuale accettazione umana con motivazione e scadenza.

Non nascondere rischi in paragrafi narrativi. Non usare “mitigato” senza evidenza.

## 15. ADR

Crea ADR per decisioni significative su struttura, dati, interfacce, dipendenze, sicurezza, affidabilità, operazioni, tecnologie e invarianti di prodotto.

Ogni ADR include:

- titolo e ID monotono;
- stato `proposed | accepted | superseded | rejected`;
- data e owner;
- implementazione `none | partial | complete`;
- task e ADR sostituite;
- contesto e forze;
- decisione precisa;
- alternative;
- conseguenze positive, negative e neutrali;
- rollout e rollback;
- evidenze e gate di rivalutazione.

Non marcare `accepted` una scelta non autorizzata. Le raccomandazioni dell'analisi nascono come `proposed`.

## 16. Checker documentale

Integra un checker leggero e offline nel sistema esistente. Deve verificare, proporzionatamente al repository:

- documenti core presenti;
- link locali validi;
- ID macro unici;
- ID micro unici;
- parent macro esistenti;
- coerenza degli ID tra roadmap e backlog;
- Macro DoD presenti;
- DoD specifica presente;
- gate review indicizzate;
- stati noti;
- assenza di transizioni manifestamente impossibili;
- stato attivo coerente con `project-state.md`, quando automatizzabile senza fragilità;
- eventuali documenti o evidenze obbligatori per il profilo di rischio.

Il checker:

- non usa rete;
- non legge segreti, database o log;
- ha dipendenze minime;
- produce errori con percorso e azione suggerita;
- gira nel comando standard locale;
- gira in CI sulle versioni supportate;
- non pretende di verificare il merito o la firma umana.

Riusa Makefile, npm scripts, task runner e workflow esistenti. Non creare sistemi paralleli senza necessità.

## 17. Definition of Ready

Un macro può diventare `ready` soltanto quando sono espliciti:

- outcome;
- utenti;
- non-obiettivi;
- dipendenze;
- baseline;
- evidenze attese;
- rischi;
- strategia di test;
- rollout e rollback;
- documenti impattati;
- approvatore umano.

Un micro può diventare `ready` soltanto quando parent, valore/problema, acceptance criteria, dipendenze, rischio, verifica, rollback e DoD specifica permettono l'esecuzione senza inventare requisiti.

Durante M00, soltanto il task corrente deve essere `in_progress`; il successivo diventa `ready` quando le sue dipendenze sono soddisfatte.

## 18. Commit e integrazione

Produci change set piccoli e comprensibili. Sequenza consigliata:

1. `docs: inventory existing project knowledge`
2. `docs: establish verified project baseline`
3. `docs: define evidence-gated target roadmap`
4. `ci: validate project brain governance`
5. `docs: prepare M00 evidence gate`

Adatta i messaggi alle convenzioni del repository. Prima di ogni commit:

- controlla `git diff --check`;
- verifica file staged;
- assicurati di non includere segreti o modifiche non correlate;
- esegui i controlli proporzionati;
- aggiorna project state, backlog e handoff.

Non effettuare merge, release, deploy o PR senza autorizzazione. Effettua push soltanto sul branch corrente se il mandato dell'utente e l'ambiente lo autorizzano esplicitamente.

## 19. Gate review M00

Prepara `docs/reviews/M00-YYYY-MM-DD.md` con:

- macro-task;
- reviewer;
- approvatore umano `pending`;
- decisione `PENDING`;
- outcome atteso vs ottenuto;
- baseline e KPI/evidenze;
- documenti migrati, mantenuti e superseded;
- task done/deferred/cancelled;
- test, checker e CI;
- review prodotto/UX;
- architettura/dati/qualità;
- performance/capacità;
- sicurezza/privacy;
- operazioni/affidabilità;
- accessibilità o N/A motivato;
- incidenti e near miss;
- assunzioni invalidate;
- debito e rischi;
- retrospettiva del processo e collaborazione AI;
- sincronizzazione di AS-IS, stato, backlog, roadmap, ADR, risk register e runbook;
- impatto sul prossimo macro;
- Definition of Ready del prossimo macro;
- raccomandazione tecnica motivata.

Lascia obbligatoriamente:

```text
Approvatore umano: pending
Decisione: PENDING
```

Non auto-approvare M00 e non avviare il macro successivo.

## 20. Brainstorming con il project owner

Dopo aver completato, verificato e possibilmente committato il Brain:

1. fermati prima di qualunque implementazione applicativa;
2. presenta una sintesi executive dell'AS-IS;
3. mostra rischi, debito, opportunità, assunzioni, contraddizioni e decisioni proposte;
4. mostra roadmap e ordine raccomandato;
5. spiega perché l'ordine riduce rischio o aumenta valore;
6. indica quali macro sono bloccati da informazioni mancanti;
7. avvia un'intervista strutturata al project owner.

Fai massimo tre domande per volta. Parti dalle decisioni con maggiore impatto sul piano:

- obiettivo reale e successo del prodotto;
- utenti e pain point;
- comportamenti che non devono cambiare;
- requisiti impliciti o non documentati;
- priorità business;
- dati e source of truth;
- ambienti e vincoli operativi;
- rischio tollerabile;
- SLA/SLO, RPO/RTO;
- sicurezza, privacy e compliance;
- budget, tempi e capacità del team;
- strategia di rilascio;
- metriche di prodotto disponibili;
- decisioni architetturali controverse;
- cosa deve essere esplicitamente escluso;
- dipendenze o stakeholder esterni.

Per ogni risposta:

1. classificala come fatto, requisito, decisione, assunzione, rischio o preferenza;
2. aggiorna il documento canonico corretto;
3. aggiorna roadmap e backlog quando cambia priorità o scope;
4. crea o aggiorna ADR proposte quando serve;
5. segnala l'impatto sulle evidenze e sul prossimo macro;
6. non riscrivere retroattivamente l'AS-IS;
7. conserva i punti ancora irrisolti.

Quando le decisioni fondamentali sono state affrontate:

- aggiorna la gate review;
- riepiloga modifiche e trade-off;
- chiedi esplicitamente `GO / RECYCLE / HOLD / STOP`.

Solo dopo un `GO` umano puoi:

1. registrare nome/data/motivazione;
2. chiudere M00;
3. portare il macro successivo a `in_progress`;
4. promuovere soltanto il primo micro-task a `ready`;
5. iniziare implementazione su successiva istruzione esplicita.

## 21. Definition of Done dell'incarico

L'incarico è concluso soltanto quando:

- istruzioni locali e stato Git sono stati verificati;
- documentazione esistente è inventariata;
- migration map presente;
- nessuna perdita informativa silenziosa;
- AS-IS verificato e datato;
- decisioni, TO-BE, piano e assunzioni separati;
- Product Brain indicizzato e navigabile;
- project state rappresenta lo stato reale;
- roadmap per outcome presente;
- backlog prioritizzato e con dipendenze;
- ogni macro ha Macro DoD;
- ogni micro ha DoD specifica;
- risk register e ADR presenti;
- threat model e documenti operativi proporzionati;
- strategia di test e comando standard documentati;
- checker e CI verdi;
- suite esistente ancora verde o failure preesistenti documentate con evidenza;
- nessun segreto, dato reale o log nel diff;
- commit atomici e handoff presenti;
- review M00 preparata;
- approvatore e decisione restano pending;
- nessun cambiamento applicativo fuori scope;
- brainstorming con il project owner avviato;
- macro successivo non avviato senza GO.

## 22. Formato della consegna prima del brainstorming

La consegna deve includere:

1. **Outcome**: cosa è stato costruito;
2. **Baseline**: commit, branch, ambiente e data;
3. **Migrazione documentale**: mantenuto, sostituito, archiviato;
4. **AS-IS executive**: prodotto, architettura, dati e operazioni;
5. **Top finding**: severità, evidenza e impatto;
6. **Rischi**: aperti, mitigati, bloccanti;
7. **TO-BE**: principi e principali trade-off;
8. **Roadmap**: macro e dipendenze;
9. **Prossimo macro raccomandato**: motivazione e DoR;
10. **Verifiche**: comandi e risultati;
11. **Git**: commit, push e working tree;
12. **Decisioni richieste**: massimo tre domande iniziali;
13. **Gate**: raccomandazione tecnica, decisione PENDING.

## 23. Avvio

Inizia ora con questo ordine:

1. leggi integralmente le istruzioni locali;
2. controlla Git e il worktree;
3. crea un piano di lavoro M00.01–M00.05;
4. inventaria documentazione e codebase;
5. dichiara classificazione, fonti e file che prevedi di modificare;
6. esegui M00 in piccoli change set;
7. verifica continuamente;
8. prepara il gate;
9. fermati per il brainstorming e l'approvazione umana.

Non limitarti a produrre un report: costruisci il Project Brain nel repository. Non limitarti a creare file: verifica e riconcilia il contenuto. Non limitarti a eseguire il piano: studia gli effetti e ripianifica usando le evidenze.
