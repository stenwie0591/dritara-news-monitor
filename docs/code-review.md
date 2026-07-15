# Code review completa

Data audit: 14 luglio 2026. Baseline iniziale: 146 test superati con 60 warning. Gli elementi sono ordinati per impatto, non per facilità.

## Critici / P0

| Finding | Impatto | Stato / remediation |
|---|---|---|
| Startup senza inizializzazione DB | Fresh install poteva fallire con `no such table` | Corretto: `main.py` chiama `init_db()` |
| Metadata scoring salvati con `str()` ma letti come JSON | Export CSV e fallback potevano fallire | Corretto con i setter JSON del modello e test |
| `/feedadd` non supportava nomi composti e ometteva `category` | Comando documentato non affidabile | Corretto e coperto da regressione |
| Analisi keyword iterava la stringa JSON carattere per carattere | Suggerimenti editoriali errati | Corretto usando `get_keyword_matches()` |
| SSRF persistente via feed e redirect | Accesso a servizi LAN/localhost dal Raspberry | Mitigato in applicazione: connect DNS-pinned, peer/hop validati, no proxy/retry/auto-redirect e cap/quota; firewall host demandato al deploy verificato |
| Pubblicazione non idempotente | Riga bloccata o doppio post dopo crash | Aperto: message id, retry persistito, claim atomico |
| Pipeline giornaliera non riprendibile | Stato parziale non recuperato | Aperto: `DigestRun` persistito per fase |

## Alti / P1

- Segreti locali erano mode `0644`: il bootstrap ora rifiuta file non `0600` e symlink; OAuth/backup/log applicano mode restrittivi e la redazione pre-sink è coperta da contract test (M01.05). I token vanno ruotati se la macchina è multi-user o i file sono stati copiati.
- RSS resource exhaustion: corretto con streaming 2 MiB/feed, quota 32 MiB/run, 200 entry, field limits e timeout dell'intera redirect chain (M01.04).
- Input RSS/utente in Telegram: corretto con renderer HTML centralizzato, escaping di testo/attributi, filtro control/bidi, link HTTP(S) senza credenziali e contract/abuse test (M01.03).
- Lo stato `publishing` fallito resta bloccato fino al restart; dopo il restart lo slot può essere già passato.
- `_save_pending` può generare righe duplicate su riesecuzione. Servono unique constraint e upsert idempotenti.
- Google Drive e SQLite sync bloccano bot/health. Spostare adapter sincroni con `asyncio.to_thread` e separare i use case.
- Backup del DB live non garantisce consistenza. Usare SQLite backup API/snapshot.
- Il health check è liveness, non readiness.
- Config/env sono duplicati e letti all'import, con errori poco diagnostici.
- Nessuna migrazione schema, foreign key esplicite, enum/check constraint o uniqueness per statistiche/coda.

## Medi / P2

- CSV formula injection: mitigata per i campi testuali con prefisso sicuro; mantenere test dedicati.
- Autorizzazione bot: corretta con principal `user_id + chat_id + private chat`, inclusi negative test e callback policy.
- Gli errori provider attraversano il patcher Loguru con redazione pre-sink; un contract test dimostra che il token completo non raggiunge il file di log (M01.05). La centralizzazione strutturale del client resta M05.
- Scoring è calcolato due volte per articolo; dedup fuzzy è O(n²); il controllo storico usa query N+1.
- `config/settings.yaml` è in drift rispetto alle costanti hard-coded.
- Retention Drive non definita: backup e CSV possono sopravvivere al cleanup locale di 90 giorni.
- Dockerfile/Compose sono vuoti e il service systemd citato dal README non esiste.
- Section3 viene calcolata ma non entra nel workflow editoriale attivo; fallback e documentazione non coincidono.

## Qualità e manutenzione

- La CI ora installa lock transitivi con hash ed esegue audit vulnerabilità e `pip check`; packaging moderno, lint/type/coverage e SBOM restano pianificati.
- Dev dependencies e tool di lock/audit sono dichiarati, bloccati e provati con clean install.
- `bot.py` (~1050 LOC), `scheduler.py` (~480) e `sender_telegram.py` (~440) sono god-module.
- Nessun test diretto per scheduler, Drive, health e lifecycle; test prevalentemente mocked.
- Uso di `datetime.utcnow()` genera warning su Python 3.13; la migrazione a UTC aware richiede una decisione coerente su DB e confronti.
- Diversi `except Exception` fanno apparire riusciti job falliti.

## Aspetti positivi

SQLModel parametrizza le query, YAML usa `safe_load`, non sono emersi `eval`, shell o subprocess pericolosi. Lo scope OAuth Drive è limitato a `drive.file`; i segreti non risultano tracciati da Git; fetch concorrente e suite unit sono una buona base per la stabilizzazione.

## Tracciabilità remediation

| Area finding | Micro-task |
|---|---|
| config/import, auth, rendering, SSRF, segreti | M01.01–M01.05 |
| schema, backup, constraint e dati legacy | M02.01–M02.07 |
| coda, claim, duplicate publish e `publishing` recovery | M03.01–M03.06 |
| digest, scheduler, health, Drive bloccante e osservabilità | M04.01–M04.07 |
| god-module, scoring doppio/N+1/O(n²), packaging e supply chain | M05.01–M05.07 |
| Section3, UX e ranking | M06.01–M06.07 |

Lo stato operativo non si deduce da questa tabella: verificare [project state](project-state.md) e [backlog](to-be/backlog.md). Nuovi finding ricevono un task o un rischio prima del gate.
