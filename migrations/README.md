# Migrazioni SQLite

Alembic è configurato senza URL predefinito: ogni comando deve ricevere un
database esplicito. Lo startup applicativo continua a non eseguire migrazioni.

M02.01 usa soltanto database temporanei e la fixture sintetica versionata. Un
database legacy può essere stamped solo dopo il fingerprint semanticamente
esatto previsto da `src/schema_baseline.py`. Il runner operativo, i preflight e
il lock esclusivo appartengono a M02.02.

Esempio esclusivamente su una copia temporanea:

```bash
.venv/bin/alembic -c alembic.ini -x db_url=sqlite:////tmp/copia.db upgrade head
```

Non eseguire comandi sul DB runtime senza snapshot, checksum, dry-run, restore
provato e approvazione esplicita. Il downgrade della baseline è disabilitato:
per uno schema legacy il rollback corretto è il restore dello snapshot.
