# Backup and restore

M02.03 stabilisce primitive e drill; M04.06 automatizza off-loop, retention e periodicità. Le evidenze confluiscono nei rispettivi gate.

## Gap AS-IS

Il file SQLite live viene letto e caricato su Drive; non c'è snapshot API, checksum, retention, ACL audit o restore drill.

## Standard target

- SQLite backup API con servizio fermo o snapshot consistente;
- file mode 0600, SHA-256 e metadata schema/app version;
- copie giornaliere 7 giorni, settimanali 8 settimane come proposta da approvare;
- Drive folder privata, niente link sharing, ACL review trimestrale;
- restore mensile automatizzato su directory isolata: hash, quick_check, FK check, schema head, smoke query;
- RPO/RTO da definire dopo misura; obiettivo iniziale proposto RPO 24h, RTO 2h.

Un upload riuscito non equivale a un backup verificato.
