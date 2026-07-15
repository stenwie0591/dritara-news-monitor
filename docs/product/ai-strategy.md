# AI strategy

## Ruolo

AI come assistente di retrieval/ranking/curatela; mai approval o publish. Fallback deterministico sempre disponibile.

## Pipeline target

1. fetch sicuro e parsing deterministico;
2. canonical URL + fingerprint + embedding cluster;
3. hard gate freshness/safety/duplicate;
4. reranker strutturato sui top-N;
5. output schema: theme, territory, value_type, confidence, rationale, proposed angle;
6. editor edit/confirm;
7. eventi e feedback versionati.

## Data contract

Persistire candidate universe, exposure rank, features/policy/model/prompt version, decision actor/reason/time, preview edit e delivery outcome. Non usare deferred/timeout come label negative. Split temporale train/validation/test; supporto minimo e shrinkage per fonte/keyword.

## Sicurezza

RSS è delimitato come dati, non istruzioni; structured output validato; nessun tool/network autonomo dal modello; URL e claim verificati da adapter deterministici; prompt/output non includono segreti; PII redatta; provider sostituibile.

## Promotion gate

Shadow 3–4 settimane e almeno 500–1.000 decisioni pulite. Confronto Precision@4, NDCG@4, audit recall, coverage, calibration, latenza e costo. Rollback immediato a baseline se degrada guardrail o fallisce schema.

## Budget da definire

Provider/model, costo giornaliero massimo, latency p95, retention prompt/output e licenza/copyright dei contenuti RSS. Nessuna dipendenza provider va inserita nel domain.
