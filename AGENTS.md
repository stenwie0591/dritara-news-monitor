# Dritara News Monitor — guida per agenti AI

Questo file è il punto di ingresso operativo per qualunque agente che lavori nel repository.

## Prima di modificare

1. Leggi `docs/README.md`, `docs/project-state.md`, `docs/governance/delivery-framework.md` e `docs/ai-handoff.md`.
2. Controlla `git status --short`: non sovrascrivere modifiche non correlate.
3. Non leggere, stampare o committare `.env`, `credentials_oauth.json`, `token_drive.json`, database o log.
4. Considera il DB la source of truth a runtime; i YAML servono solo al seed iniziale.
5. Mantieni compatibilità con Python 3.11+ e Raspberry Pi ARM64.

## Comandi standard

```bash
make setup-dev
make test
make check
```

La Definition of Done canonica è in `docs/governance/definition-of-done.md`. Oltre alla DoD globale, ogni micro-task ha una DoD specifica nel backlog.

## Regole di delivery

- Lavorare solo su un micro-task `ready` del macro attivo, citandone l'ID; lavoro emergente riceve prima un ID.
- Quando nessun macro è attivo, la sola manutenzione documentale di governance può usare un task `GOV.NNN` autorizzato dal project owner secondo ADR-004; non modifica runtime/prodotto/dati e non autorizza il macro successivo.
- Un solo macro-task è `in_progress`; non implementare il successivo senza gate umano `GO`.
- Gli agenti possono preparare evidenze e review ma non auto-approvare un gate o un contenuto pubblico.
- Alla chiusura di ogni micro aggiornare evidenze, AS-IS e handoff; alla chiusura macro usare il template di gate e riesaminare prodotto, architettura, performance, sicurezza e operazioni.
- Documentazione e ripianificazione sono condizioni di `GO`, non attività successive.

## Confini architetturali

- Preferire un monolite modulare: dominio e use case non devono dipendere da Telegram, Drive o HTTP.
- Nessuna nuova configurazione globale letta all'import; convergere verso settings tipizzati e dependency injection.
- Le operazioni esterne devono avere timeout, limiti, retry controllati e stato persistito.
- Ogni workflow schedulato deve essere idempotente e riprendibile dopo un crash.
- Non introdurre microservizi o Postgres senza un requisito esplicito di scala/concorrenza.

## Sicurezza

- I contenuti RSS sono input non attendibili, anche se il feed è configurato da un admin.
- Non interpolare input RSS in Markdown/HTML/CSV senza escaping o sanitizzazione.
- Non seguire redirect verso indirizzi privati, loopback, link-local o metadata endpoint.
- I file segreti devono avere mode `0600`; directory di backup `0700`.
- Non loggare URL Telegram completi: contengono il token del bot.

## Modifiche ad alto rischio

Richiedono piano, migrazione/rollback e test dedicati: schema DB, stati della coda, algoritmo di scoring, ordine/semantica editoriale, retention, autenticazione admin, formato dei messaggi pubblici.

## Documentazione viva

- Stato corrente: `docs/architecture-as-is.md`
- Baseline e lavoro in corso: `docs/project-state.md`
- Handoff tra agenti: `docs/ai-handoff.md`
- Finding e debito: `docs/code-review.md`
- Decisioni future: `docs/roadmap-to-be.md`
- Task eseguibili: `docs/to-be/backlog.md`
- Framework e DoD: `docs/governance/delivery-framework.md`, `docs/governance/definition-of-done.md`
- Gate storici: `docs/reviews/`
- Esercizio e incidenti: `docs/runbook.md`
- Decisioni consolidate: nuovi record in `docs/adr/`
