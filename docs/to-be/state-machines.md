# State machines target

La persistenza/cutover Publication appartiene a M03.01–M03.06; DigestRun a M04.01–M04.03. I diagrammi diventano AS-IS solo dopo test, cutover e gate del macro corrispondente.

## Digest

```text
started → fetched → scored → candidates_ready → admin_notified
                                                   ↓
                                      awaiting_approval → scheduled → completed
          ogni fase → failed(phase,error) → resume dalla prima incompleta
```

Una sola `DigestRun` per data Europe/Rome. Ogni fase committa output idempotenti prima della successiva; notify/export hanno proprie chiavi idempotenti.

## Decisione editoriale

Eventi append-only: `shown`, `approve`, `reject(reason)`, `defer(until)`, `edit`, `confirm_preview`, `cancel`. Callback Telegram e digest version sono unique: doppio tap e comando stale non cambiano la proiezione due volte.

## Publication

```text
scheduled → claimed → dispatching → delivered
                │          ├→ definite_reject → failed_retryable → scheduled
                │          └→ ambiguous/crash → delivery_unknown
                └→ lease scaduta prima della rete → scheduled

delivery_unknown --manuale--> delivered | scheduled | cancelled
```

Invarianti:

- approval actor/time/version obbligatori;
- idempotency key lifetime `destination + article_id` unique;
- `delivery_unknown` mai selezionata dal worker automatico;
- commit `dispatching` e attempt iniziato prima della chiamata Telegram;
- `delivered` terminale e con message ID, salvo record legacy marcato;
- `scheduled_for` UTC derivato da Europe/Rome; slot passato va al prossimo slot futuro.
