# {{PROJECT_NAME}} Project Brain

Fonte canonica per comprendere e governare il progetto. Ultima verifica: `{{DATE}}`.

## Regola di lettura

- **AS-IS**: verificato nel codice, nei test, nei dati o nel runtime.
- **DECISIONE**: scelta accettata, anche se non ancora implementata.
- **TO-BE**: design target o proposta.
- **PIANO**: sequenza con criteri di accettazione.

Non dedurre che una decisione o un TO-BE siano già implementati. Verificare sempre `project-state.md`.

## Percorso minimo

1. `project-state.md`
2. `governance/delivery-framework.md` e `governance/definition-of-done.md`
3. `ai-handoff.md`
4. `architecture-as-is.md`
5. `roadmap-to-be.md` e `to-be/backlog.md`
6. `governance/risk-register.md`
7. `adr/` e `reviews/`

## Gerarchia delle fonti

Definire esplicitamente quale fonte prevale per comportamento runtime, stato operativo, piano e decisioni. In assenza di una regola più specifica: codice/test descrivono il comportamento verificabile; project state il lavoro attivo; gate e ADR le decisioni; roadmap e backlog il futuro.
