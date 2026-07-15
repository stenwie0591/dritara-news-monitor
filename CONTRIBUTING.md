# Contributing

Aprire cambi piccoli e focalizzati. Descrivere comportamento precedente, comportamento atteso, rischio e verifica. Per schema DB, workflow editoriale o sicurezza includere migrazione e rollback.

```bash
make setup-dev
make check
```

Aggiornare documentazione e ADR quando cambia una decisione architetturale. Non includere segreti, database, token, log o output di produzione in commit e test fixture.

Prima di iniziare leggere `docs/project-state.md` e il [delivery framework](docs/governance/delivery-framework.md), quindi scegliere un micro-task `ready` del macro attivo. Verificarne la Definition of Ready, assegnare owner ed evidenze attese e mantenere il WIP entro 2.

Flusso: `ready → in_progress → in_review → done`. Un PR/change set deve citare macro e micro ID e descrivere outcome, acceptance criteria, rischio, test, sicurezza, performance, osservabilità, document impact, rollout e rollback. Lavoro emergente riceve un ID; non viene nascosto nello scope corrente.

Un cambiamento di schema richiede migration, fixture legacy sintetica, dry-run e rollback; non usare un DB reale come fixture. Le altre estensioni risk-based sono nella [Definition of Done](docs/governance/definition-of-done.md).

Alla fine del macro si compila una gate review: outcome/KPI, review multidisciplinare, retrospettiva, rischi e documenti. Solo un approvatore umano può registrare `GO`; prima di allora il macro successivo non viene implementato.
