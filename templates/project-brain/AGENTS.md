# {{PROJECT_NAME}} — guida per agenti AI

## Prima di modificare

1. Leggi `docs/README.md`, `docs/project-state.md`, `docs/governance/delivery-framework.md` e `docs/ai-handoff.md`.
2. Controlla lo stato Git e non sovrascrivere modifiche non correlate.
3. Non leggere, stampare o committare segreti, dati reali o log senza necessità e autorizzazione esplicite.
4. Verifica l'AS-IS nel codice o nel runtime prima di usare un TO-BE come presupposto.
5. Usa i comandi standard definiti dal progetto.

## Regole di delivery

- Lavora soltanto su un micro-task `ready` del macro attivo, citandone l'ID.
- Il lavoro emergente riceve un ID prima del merge.
- Un agente prepara evidenze ma non auto-approva gate o decisioni riservate a persone.
- Documentazione, test, rollout e rollback fanno parte del task.
- Cambi ad alto rischio richiedono piano, test dedicati e recovery provato.

## Vincoli specifici

Compilare qui runtime supportati, confini architetturali, invarianti di prodotto, policy di sicurezza e operazioni vietate.
