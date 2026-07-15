# Data model — AS-IS

## Tabelle

| Tabella | Scopo | Stato |
|---|---|---|
| `feedsource` | catalogo feed e health corrente | attiva |
| `article` | soli articoli non discarded dallo scorer | attiva |
| `publishqueue` | review e pubblicazione legacy | attiva, duplicati osservati |
| `keywordconfig` | keyword runtime | attiva |
| `keywordweighthistory` | rollback pesi | vuota nello snapshot |
| `feedstats` | yield giornaliero per feed | integrata, vuota nello snapshot |
| `digestlog` | run giornaliero | definita ma non usata |

## Invarianti effettive

- PK Article = SHA-256 dell'URL non canonicalizzato.
- URL FeedSource unique.
- FK dichiarate nello schema, ma `PRAGMA foreign_keys` risulta disabilitato nello snapshot.
- Per nuovi DB è dichiarata unique `(article_id,digest_date)` sulla queue; il DB legacy non la riceve con `create_all`.
- Stati e sezioni sono stringhe libere senza CHECK.
- Timestamp SQLite sono UTC naive o date locali a seconda del call site.

## Anomalie legacy

- 443/443 score detail e keyword matches erano repr Python, non JSON; runtime ora legge entrambi.
- 10 queue row rappresentano 5 articoli; anche la pubblicazione osservata è duplicata.
- indici dichiarati nei modelli non sono tutti presenti nel DB reale.
- nessuna schema version o policy version.

## Retention

Article/queue locali oltre 90 giorni vengono cancellati. CSV e backup Drive non hanno lifecycle, quindi la retention effettiva è indefinita.
