# Workflow — AS-IS verificato

## Digest giornaliero

```text
07:00 scheduler
  → feed attivi da SQLite
  → fetch concorrente
  → dedup solo batch
  → score (prima volta)
  → persist Article non-discarded
  → score (seconda volta) per FeedStats
  → fallback Section1
  → notify admin e ricrea pending queue
  → export CSV Drive
  → alert errori feed
```

Commit multipli avvengono prima della notifica/export. Una failure successiva non rende il job fallito ad APScheduler e lo startup può considerare la giornata conclusa perché esiste almeno un Article.

## Review

`/ok` approva posizioni e assegna slot nell'ordine digitato; tutti gli altri pending vengono differiti automaticamente. `/scarta` marca posizioni come discarded. Non esistono candidate-set version, actor/user ID, reason label o preview finale.

## Publish

```text
approved → publishing → chiamata Telegram → published
                    └→ errore: resta publishing
startup: publishing → approved automaticamente
```

L'ultimo passaggio può duplicare un post con esito Telegram ambiguo. È AS-IS ma vietato dal target ADR-002.

## Recovery e cleanup

- startup: recupera `publishing`, poi rilancia il fetch se non trova Article odierni;
- domenica 02:00: elimina queue/article oltre 90 giorni;
- domenica 02:30: legge il file SQLite live e lo carica su Drive;
- health: risponde `OK` senza controllare DB/job/backlog.

## Failure point da preservare nei test

Crash prima/dopo ogni commit, dopo `dispatching`, dopo risposta Telegram, durante Drive, doppio trigger scheduler, callback Telegram ripetuto, slot passato e cambio ora legale.
