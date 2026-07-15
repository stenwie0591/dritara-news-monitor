# ADR-002: workflow editoriale e priorità anti-duplicato

- Stato: accettato
- Data: 2026-07-14
- Implementazione: partial; la state machine e la nuova UX sono TO-BE

## Decisioni

- L'approvazione umana è sempre obbligatoria e include preview/conferma del contenuto pubblico.
- Gli slot restano 09:00, 13:00, 18:00 e 22:00 Europe/Rome.
- Section3 diventa Radar territoriale editor-only, non fallback del digest principale.
- L'admin può aggiungere qualunque dominio, ma non destinazioni di rete non pubbliche; ogni redirect viene rivalidato.
- Il target iniziale resta single-instance Raspberry + SQLite.
- L'AI classifica, raggruppa, spiega e propone; non approva né pubblica.
- In caso di esito Telegram ambiguo si privilegia l'assenza di duplicati.

## Semantica di delivery

Telegram non offre una idempotency key per `sendMessage`; exact-once non è dimostrabile se il processo cade dopo la ricezione Telegram ma prima del commit SQLite.

La state machine target usa `scheduled → claimed → dispatching → delivered`. Un crash o timeout ambiguo dopo `dispatching` produce `delivery_unknown`: nessun retry automatico. L'admin verifica il canale e sceglie `delivered`, `retry` o `cancel`. Solo errori sicuramente rifiutati diventano `failed_retryable` con backoff.

Ogni pubblicazione avrà chiave unica `hash(destination + article_id)`, actor/tempo/versione dell'approvazione, `scheduled_for` UTC, numero tentativi e `telegram_message_id` quando noto. Lo startup non riporterà più automaticamente `dispatching` ad `approved`.

## Conseguenze

Un contenuto può essere ritardato e richiedere riconciliazione manuale, ma non viene reinviato automaticamente quando potrebbe essere già pubblico. Questo è coerente con la priorità dichiarata “evitare duplicati”.
