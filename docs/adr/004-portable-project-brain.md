# ADR-004: Project Brain portabile e manutenzione governance

- Stato: accepted
- Data: 2026-07-15
- Owner: project owner / engineering
- Implementazione: complete
- Supersedes: none
- Task: GOV.001

## Contesto

Dopo i gate M00 e M01 il project owner ha richiesto di conservare la valutazione teorica del framework e di renderlo esportabile verso altri progetti. Il lifecycle macro non descriveva inoltre come eseguire una modifica esclusivamente documentale tra un macro chiuso e il successivo non ancora avviato, senza riaprire retroattivamente il gate o associare il lavoro a un outcome estraneo.

## Decisione

Mantenere Dritara Evidence-Gated Delivery come framework interno, pubblicarne valutazione e guida di adozione e fornire uno starter kit neutro.

Introdurre gli ID `GOV.NNN` per manutenzione emergente della sola governance quando autorizzata dal project owner. Un task GOV può modificare documenti di metodo, template e relativi checker, ma non runtime, prodotto, dati, gate storici o stato dei macro. Deve avere outcome, scope, rischio, verifica ed evidenze; non autorizza l'avvio del macro successivo e non sostituisce un micro-task di delivery.

## Alternative

- Riaprire M00: altera retroattivamente un gate storico già concluso.
- Associare il lavoro a M02: confonde governance portabile con l'outcome dati/migrazioni.
- Eseguire la modifica senza ID: viola la tracciabilità del lavoro emergente.
- Trasformare il framework in uno standard rigido: aumenterebbe la cerimonia e renderebbe il kit inadatto a rischi e team diversi.

## Conseguenze

L'analisi resta versionata e il framework può essere riusato senza copiare contenuti Dritara-specifici. Compare un secondo namespace di lavoro, volutamente limitato e non utilizzabile per aggirare gate o priorità. Il kit dovrà essere mantenuto come baseline portabile, senza sincronizzazione automatica distruttiva verso i progetti derivati.

## Rollout e rollback

GOV.001 aggiunge assessment, guida, starter kit e link canonici. `make check` verifica il Brain Dritara; la checklist dello starter kit ne verifica manualmente la neutralità. Rollback: rimuovere kit e documenti e supersedere questa ADR; nessun effetto su runtime o dati.

## Evidenze e gate

Decisione richiesta esplicitamente dal project owner il 2026-07-15. Evidenze: diff documentale, link check, suite `make check` e handoff GOV.001. M01 resta chiuso e M02 resta non avviato.
