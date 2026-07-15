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

## Versionamento schema

- Alembic 1.18.5 e la revisione `0001_legacy_baseline` sono presenti da M02.01.
- Su un DB fresh la revisione crea le sette tabelle e gli indici dichiarati dai modelli; un test confronta il manifest con `SQLModel.metadata`.
- Il fingerprint `b6f71f…3b24` descrive soltanto la fixture legacy sintetica versionata: non certifica il DB di produzione.
- Uno schema legacy deve essere verificato prima dello stamp; schema vuoto/divergente viene rifiutato dalla primitive read-only senza creare `alembic_version`.
- L'ambiente Alembic richiede un URL SQLite con path assoluto e non ha un database predefinito.
- Lo startup runtime continua a usare `create_all()` e non invoca Alembic; preflight, runner e rimozione di `create_all()` come upgrade mechanism appartengono a M02.02/M02.06.

## Anomalie legacy

- 443/443 score detail e keyword matches erano repr Python, non JSON; runtime ora legge entrambi.
- 10 queue row rappresentano 5 articoli; anche la pubblicazione osservata è duplicata.
- indici dichiarati nei modelli non sono tutti presenti nel DB reale.
- il DB reale non ha ancora una schema version verificata; la baseline è provata solo su fixture sintetiche/temp.

## Retention

Article/queue locali oltre 90 giorni vengono cancellati. CSV e backup Drive non hanno lifecycle, quindi la retention effettiva è indefinita.
