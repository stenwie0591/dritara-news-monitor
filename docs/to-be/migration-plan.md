# Database migration plan

Questo piano è eseguito da M02.01–M02.07 e costituisce evidence del gate M02; nessun passo sul DB reale è autorizzato dalla sola presenza del documento.

## Strategia

Expand → backfill/quarantine → dual-write → cutover → enforce → contract. Nessuna migrazione automatica allo startup.

## Revisioni previste

1. `0001_legacy_baseline`: fingerprint esatto dello schema legacy; stamp solo dopo verifica.
2. `0002_expand_workflow_telemetry`: tabelle additive `digest_run`, phase attempt, exposure, decision, delivery, attempt, quality issue e conflict.
3. `0003_backfill_legacy`: JSON legacy normalizzato; duplicati copiati integralmente in quarantena; `publishing` proiettato `delivery_unknown`.
4. `0004_enforce_invariants`: batch rebuild SQLite per FK/CHECK/UNIQUE dopo preflight verde.
5. `0005_contract_legacy`: molto più tardi, dopo un ciclo retention e zero reader legacy.

## Procedura operativa

1. stop servizio e lock esclusivo;
2. spazio libero >=3× DB;
3. snapshot con SQLite backup API, mode 0600 e SHA-256;
4. dry-run su copia e `quick_check`/`foreign_key_check`;
5. upgrade una revisione alla volta con contatori/invarianti;
6. avvio release A dual-write; confronto almeno una settimana;
7. release B cutover con feature flag;
8. rollback primario: stop e restore atomico snapshot verificato.

I duplicati non vengono cancellati silenziosamente. Survivor: precedenza published > publishing > approved > pending > deferred > discarded; tutte le righe e gli attempt osservati restano in conflict/audit.

## Scaffold sicuro prima del DB reale

Alembic, fixture schema legacy sintetica, preflight read-only, migration runner con path esplicito, restore verifier e CI su fresh/legacy DB. Non applicare stamp/backfill/constraint al DB reale senza copia produzione.
