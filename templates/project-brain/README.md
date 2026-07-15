# Evidence-Gated Project Brain starter kit

Baseline portabile del Dritara Evidence-Gated Delivery Framework. I file contengono segnaposto e non includono codice, dati, segreti, rischi o decisioni specifiche di Dritara.

Per un progetto brownfield già esistente è preferibile usare il prompt orchestratore `templates/PROJECT_BRAIN_BOOTSTRAP_PROMPT.md`: l'agente inventaria e riconcilia la documentazione prima di sostituirla, quindi costruisce il Brain e si ferma al gate umano.

## Installazione

Da una copia del repository Dritara:

```bash
mkdir -p /percorso/nuovo-progetto
cp -R templates/project-brain/. /percorso/nuovo-progetto/
```

Se il repository esiste già, esaminare prima ogni collisione: non sovrascrivere `AGENTS.md` o documenti locali senza merge consapevole.

## Personalizzazione obbligatoria

1. Sostituire `{{PROJECT_NAME}}`, `{{DATE}}`, owner, approvatore e comandi.
2. Verificare il sistema reale e compilare `architecture-as-is.md`.
3. Definire Product Goal, rischi e 3–6 macro-outcome.
4. Dettagliare soltanto il primo macro in micro-task eseguibili.
5. Adattare DoD e controlli risk-based al dominio.
6. Collegare un comando unico di verifica alla CI.
7. Approvare il primo macro soltanto con una gate review umana.

## Definition of Done del bootstrap

- nessun segnaposto rilevante è rimasto;
- AS-IS e stato riportano fonte e data;
- ogni task ha ID, dipendenze e DoD misurabile;
- rischi e decisioni hanno owner;
- link e comandi sono verificati;
- il Brain distingue fatti, decisioni, TO-BE e piano;
- nessun contenuto Dritara-specifico è presentato come fatto del nuovo progetto.

Il kit è una baseline da adattare, non una dipendenza da aggiornare automaticamente.
