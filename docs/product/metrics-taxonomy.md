# Metrics taxonomy

Ogni metrica richiede evento sorgente, denominatore e finestra. Non calcolare precision/recall dal legacy DB.

| Metrica | Formula | Fonte target | Finestra |
|---|---|---|---|
| approval precision | distinct approved / distinct explicitly reviewed | decision events | giorno/28gg |
| Precision@4 | approvati tra primi 4 / 4 mostrati | exposure+decision | giorno/28gg |
| audit recall proxy | rilevanti nel campione esclusi / campione | audit decision | settimana |
| freshness | percentuale published <24/48/72h | article+delivery | 28gg |
| duplicate rate | delivery duplicate / delivered | delivery audit | lifetime/28gg |
| source share | published per fonte / total published | delivery+article | 28gg |
| review time | decision_at - shown_at, mediana/p90 | exposure+decision | 7/28gg |
| slot reliability | delivered entro tolleranza / scheduled | delivery | 28gg |
| feed yield | eligible / parsed | phase telemetry | 28gg |
| useful stories | delivered con value label e approval | decision+delivery | settimana |

Target iniziali accettati: duplicate rate 0; 100% decisioni tracciate. Proposte da validare dopo baseline: p90 review <10 min, precision digest >=70%, fonte <=25%/28gg.

Follower/reach/engagement sono outcome audience. CTR/forward/save e feedback utile vanno associati a publication ID con tracking privacy-conscious.
