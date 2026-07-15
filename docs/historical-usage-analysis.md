# Analisi utilizzo e storico

Data analisi: 14 luglio 2026. Fonte: `data/dritara.db`, interrogato in sola lettura. Non sono stati estratti o riportati titoli e URL.

## Limite fondamentale

Lo snapshot locale non è lo storico di produzione: contiene un solo digest, dell'8 marzo 2026. Il Drive connesso non espone i backup/CSV creati dal Raspberry. Le conclusioni seguenti diagnosticano quel run e il modello dati; non sono trend longitudinali.

## Snapshot

| Metrica | Valore |
|---|---:|
| Articoli persistiti | 443 |
| Feed configurati/attivi | 30/30 |
| Section1 | 9 (2,0%) |
| Section2 | 122 (27,5%) |
| Section3 | 312 (70,4%) |
| Articoli distinti in coda | 5 |
| Righe di coda | 10 |
| DigestLog / FeedStats / history | 0 / 0 / 0 |

Il 94,6% degli articoli da feed livello 3 finisce in Section3. I primi tre feed generano il 53,7% di tutti gli articoli e il 73,1% di Section3: il radar territoriale è molto voluminoso e concentrato, ma raramente diventa segnale tech.

## Freschezza

L'età mediana rispetto alla data dichiarata dal feed è 2,31 giorni; il 23,5% ha almeno sette giorni e il massimo supera ampiamente un anno. I cinque candidati in coda hanno mediana 3,57 giorni e nessuno è più fresco di 24 ore. La freshness deve diventare un hard gate/configurazione esplicita prima del ranking.

## Evidenza di duplicazione

Ogni articolo in coda compare esattamente due volte, con posizione/data duplicate. Anche l'unico articolo marcato pubblicato ha due righe `published` con timestamp distanti circa 12 minuti: forte evidenza di una doppia pubblicazione, coerente con la riesecuzione non idempotente del digest.

Sono state aggiunte una barriera applicativa e una unique constraint per nuovi database. Il database esistente richiede migrazione con quarantena dei duplicati, non cancellazione silenziosa. La garanzia anti-duplicato completa richiede la state machine descritta in ADR-002.

## Qualità del dato

- I 443 campi `score_detail` e `keyword_matches` non sono JSON validi, ma rappresentazioni Python legacy. Il runtime ora li legge in modo compatibile e scrive JSON valido per i nuovi record.
- La configurazione keyword non è versionata ed è successiva agli articoli dello snapshot: non si può ricostruire fedelmente la policy usata.
- Non vengono conservati raw scartati, candidate exposure, motivazioni, tempi di review o universo escluso; precision e recall non sono calcolabili seriamente.
- Il DB reale non contiene tutti gli indici dichiarati nei modelli, ha FK disattivate e journal mode `DELETE`: serve una migrazione, non `create_all()`.

## Conseguenze

1. Section3 non entra nel digest quotidiano: diventa Radar territoriale editor-only e possibile sintesi settimanale.
2. Prima del training AI servono 4–8 settimane di telemetria corretta e almeno 500–1.000 decisioni editoriali distinte.
3. Il funnel da persistere è `raw → parsed → deduped → eligible → shown → decision → approval → attempt → delivered`.
4. Ranking: hard gate di sicurezza/freschezza, pertinenza, novelty e diversità; lo score assoluto attuale non equivale a utilità.
5. Il cap per fonte deve continuare a scorrere la classifica fino a riempire la shortlist, non filtrare un top-N già troppo concentrato.

## Dato necessario

Per completare l'analisi storica serve una copia in sola lettura del DB di produzione recente oppure accesso alla cartella Drive contenente `dritara_backup_*.db`/CSV. Prima dell'analisi verrà creata una copia di lavoro e non verrà modificato l'originale.
