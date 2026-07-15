# AI handoff protocol

## Avvio sessione

1. Leggere `AGENTS.md`, project state, framework e documento del task.
2. Controllare lo stato Git e preservare modifiche non correlate.
3. Verificare l'AS-IS prima di assumere vero un TO-BE.
4. Proteggere segreti, dati reali e log.
5. Prendere un solo task `ready` e dichiarare file, rischio ed evidenze.

## Handoff in uscita

Riportare sempre:

- ID, owner e stato;
- obiettivo e scope effettivo;
- file e comportamento cambiati;
- invarianti preservate;
- test, benchmark o drill con risultato;
- migrazione, flag e rollback;
- rischi e debito residui;
- documenti e stato sincronizzati.

## Ultimo handoff

- ID/stato/data: pending.
- Outcome: pending.
- Evidenze: pending.
- Rischi/rollback: pending.
