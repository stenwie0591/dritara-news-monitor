# Security policy

Non aprire issue pubbliche contenenti token, chat/user ID, file OAuth, database, log o materiale editoriale riservato. Contattare privatamente il maintainer del repository e indicare impatto, prerequisiti e riproduzione minima redatta.

## Risposta iniziale

Obiettivo operativo: conferma entro 3 giorni lavorativi per finding critici/alti e 7 giorni per gli altri. La priorità segue impatto su credenziali, pubblicazione non autorizzata/duplicata, accesso rete interna, perdita dati e disponibilità.

## Regole per contributor e agenti

- segreti esclusi da Git e mode 0600;
- nessun DB/log di produzione in fixture o output;
- RSS, Telegram e output AI sono input non attendibili;
- nessuna migrazione reale senza backup/restore verificato;
- revocare subito una credenziale sospetta: cancellare il file non revoca il token.

Threat model, stato dei controlli e incident response sono in `docs/security/threat-model.md` e `docs/runbook.md`.
