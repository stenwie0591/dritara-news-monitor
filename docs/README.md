# Dritara Project Brain

Questa cartella è la fonte canonica per comprendere il progetto. Ultima verifica: 15 luglio 2026, branch `feature/codex_init`; M01 è chiuso e M02 non è ancora avviato.

## Regola di lettura

Ogni informazione appartiene a una categoria:

- **AS-IS**: verificata nel codice, DB o test correnti.
- **DECISIONE**: scelta accettata, anche se non ancora implementata.
- **TO-BE**: design target o proposta.
- **PIANO**: sequenza di lavoro con acceptance criteria.

Non dedurre che una decisione sia già implementata. Verificare sempre [project-state.md](project-state.md).

## Percorso minimo per un agente AI

1. [Project state](project-state.md)
2. [Delivery framework](governance/delivery-framework.md) e [Definition of Done](governance/definition-of-done.md)
3. [AI handoff](ai-handoff.md)
4. [Codebase map](as-is/codebase-map.md)
5. [Workflow as-is](as-is/workflows.md)
6. [Data model](as-is/data-model.md)
7. [Roadmap](roadmap-to-be.md) e [backlog eseguibile](to-be/backlog.md)

## Catalogo

### Stato e governance

- [Project state](project-state.md) — baseline, work in progress, blocker e prossime azioni.
- [AI handoff](ai-handoff.md) — protocollo operativo per modelli e agenti.
- [Delivery framework](governance/delivery-framework.md) — lifecycle macro/micro, PDSA e gate umano.
- [Definition of Done](governance/definition-of-done.md) — qualità globale, risk-based e macro.
- [Template macro](governance/macro-task-template.md), [micro](governance/micro-task-template.md) e [gate review](governance/macro-review-template.md).
- [Risk register](governance/risk-register.md) e [gate review storiche](reviews/README.md).
- [ADR index](governance/adr-index.md) e [template ADR](governance/adr-template.md).
- [Glossario](glossary.md).

### AS-IS verificato

- [Architettura sintetica](architecture-as-is.md)
- [Mappa codebase](as-is/codebase-map.md)
- [Workflow e failure mode](as-is/workflows.md)
- [Modello dati](as-is/data-model.md)
- [Contratti esterni](as-is/contracts.md)
- [Inventario funzionale](as-is/feature-inventory.md)
- [Configurazione](configuration.md)
- [Analisi utilizzo](historical-usage-analysis.md)
- [Code review](code-review.md)

### Decisioni e TO-BE

- [Strategia prodotto](product-strategy.md)
- [Architettura target](to-be/target-architecture.md)
- [Decisione sullo stack tecnologico](to-be/technology-stack.md)
- [State machine target](to-be/state-machines.md)
- [Piano migrazioni](to-be/migration-plan.md)
- [Backlog eseguibile](to-be/backlog.md)
- [Roadmap per macro-task e gate](roadmap-to-be.md)
- [Policy editoriale](product/editorial-policy.md)
- [Tassonomia metriche](product/metrics-taxonomy.md)
- [Strategia AI](product/ai-strategy.md)

### Sicurezza e operazioni

- [Threat model](security/threat-model.md)
- [Deployment](operations/deployment.md)
- [Osservabilità](operations/observability.md)
- [Backup e restore](operations/backup-restore.md)
- [Runbook incidenti](runbook.md)
- [Strategia di test](testing.md)

## Documenti storici

`Dritara_News_Monitor_MVP_v1.0.docx` è una specifica legacy utile come contesto, ma non è authoritative rispetto a codice, ADR e project state.

## Gerarchia di stato

Il codice/test descrive il comportamento verificabile; i documenti AS-IS lo spiegano; `project-state.md` indica il lavoro attivo; roadmap e backlog pianificano; le review in `docs/reviews/` registrano le decisioni umane. Un TO-BE non è mai prova di implementazione.
