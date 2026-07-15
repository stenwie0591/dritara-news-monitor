# Feature inventory

| Feature | Stato | Note |
|---|---|---|
| RSS fetch/scoring | implementata | config parzialmente hard-coded |
| dedup batch | implementata | fuzzy O(n²) |
| dedup storico 7gg | parziale | solo filtro pre-notifica su published |
| review Telegram | implementata legacy | comandi numerici |
| publish slots | implementata | delivery non idempotente |
| feed/keyword admin | implementata | feed safe-fetch mitigato |
| Section3 Radar | decisa, non implementata | oggi persiste ma non ha UX dedicata |
| fallback Section1 | implementato legacy | da rimuovere |
| FeedStats/heartbeat | implementata | dati snapshot assenti |
| DigestLog/resume | non implementata | modello morto |
| weekly formatter | non integrata | codice/test presenti |
| Drive CSV/backup | implementata | sync, no retention/restore |
| AI reranking/rationale | non implementata | shadow mode target |
| inline preview/reason | non implementata | target prodotto |
