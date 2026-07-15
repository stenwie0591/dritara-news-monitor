# Strategia prodotto

## Tesi

Dritara News Monitor deve evolvere da aggregatore di link a servizio di intelligence editoriale: pochi segnali che aiutano il team a capire cosa conta, perché conta e quale contenuto produrre. Il business plan posiziona Dritara come media divulgativo nazionale nato dal Sud, non come rassegna stampa territoriale; l'app deve sostenere quel lavoro editoriale.

Il valore non è “più notizie”, ma trasformare rumore nazionale e locale in idee verificabili per tecnologia, lavoro, innovazione, economia e attualità.

## Esperienza target

Ogni mattina l'editor riceve 6–10 candidati freschi e diversi. Ogni card mostra:

- fonte, età, territorio, tema e confidenza;
- perché è stata selezionata;
- eventuali duplicati/coperture precedenti;
- bozza AI di “perché conta” e possibile angolo editoriale.

L'editor sceglie Approva, Scarta con motivo, Più tardi o Apri. Un'approvazione apre sempre la preview esatta del contenuto pubblico, modificabile, con slot proposto; solo la conferma finale autorizza la pubblicazione.

## Sezioni

- **Impatto sul Sud**: intersezione reale tra territorio e temi Dritara.
- **Trend da tradurre**: segnale nazionale da interpretare per il pubblico.
- **Radar territoriale**: Section3 editor-only, consultabile on demand e in sintesi settimanale. Non va rinominata artificialmente “Impatto sul Sud” tramite fallback.

Dopo quattro settimane si misura quanta parte del Radar viene promossa manualmente. Una promotion rate bassa implica campionamento/riduzione; una alta indica falsi negativi del ranking.

## North star e guardrail

North star: **storie territoriali di valore consegnate a settimana**, cioè pubblicazioni distinte approvate con un valore esplicito (impatto, opportunità, spiegazione o novelty).

Guardrail imprescindibile: **zero duplicati pubblici**.

KPI operativi iniziali:

- 100% delle decisioni tracciate con actor, timestamp e motivo;
- precision@digest e precision@4, calcolate su decisioni esplicite;
- audit settimanale di 20 esclusi per stimare recall;
- p90 review inferiore a 10 minuti;
- freschezza sotto 24/48/72 ore;
- nessuna fonte oltre il 25% dei pubblicati su 28 giorni;
- copertura di territori, temi e tipi di valore;
- digest pronto entro SLA, slot rispettati, zero delivery automatiche ambigue;
- CTR/forward/reazioni e feedback “utile/non utile” come outcome, quando disponibili.

Follower e volume non sono north star: sono outcome di qualità e distribuzione.

## Ruolo dell'AI

L'AI non approva e non pubblica. Architettura consigliata:

1. retrieval deterministico ampio e sicuro;
2. canonicalizzazione, embeddings e clustering per dedup semantico;
3. reranker ML/LLM sui top candidati;
4. output strutturato: tema, territorio, valore, confidenza, rationale e bozza;
5. editor modifica e conferma;
6. fallback deterministico se AI non disponibile.

Partire in shadow mode per 3–4 settimane. Promuovere il ranking AI solo se migliora Precision@4/NDCG senza ridurre coverage e freshness. Lo storico corrente non è un dataset supervisionato pulito: deferred e discarded non sono necessariamente giudizi negativi.

## Esperimenti

1. Telemetria e reason labels: almeno 90% dei candidati con decisione esplicita.
2. Inbox inline + preview contro comandi numerici: obiettivo -40% tempo review.
3. Radar Section3 per quattro settimane: promotion rate e categorie promosse.
4. AI shadow ranking: confronto temporale con baseline deterministica.
5. Link grezzo contro “perché conta” revisionato: CTR, feedback e costo editoriale.
6. Portfolio feed mensile: resa, unicità, coverage e falsi negativi.
7. Sintesi settimanale “cosa è cambiato / cosa fare”, aggregata per storia e non per link.

## Evoluzione infrastrutturale

Restare su Raspberry, SQLite e monolite modulare. Passare a cloud/Postgres solo con più editor, SLA/HA, più tenant o contesa misurata. Subito, invece: backup off-device consistente, restore testato, telemetria e state machine persistita.

## Tracciabilità delivery

M06.01–M06.07 realizza e misura discovery, inbox, preview, ranking, Radar, dashboard ed esperimenti. M07.01–M07.07 governa l'AI in shadow. Il gate di ciascun macro confronta outcome e guardrail con baseline e decide keep/change/drop; nessun incremento elimina l'approvazione umana.
