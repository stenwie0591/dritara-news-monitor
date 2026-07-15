# Runbook operativo

## Setup e avvio locale

```bash
python3.11 -m venv .venv
make setup-dev
cp .env.example .env
chmod 600 .env
chmod 600 credentials_oauth.json token_drive.json  # solo se presenti
make check
.venv/bin/python main.py
```

`requirements.txt` e `requirements-dev.txt` sono gli input dichiarativi; i file
`*.lock` transitivi con hash sono quelli installati. Dopo una modifica intenzionale
agli input eseguire `make lock`, riesaminare il diff e poi `make audit`. La CI blocca
hash incompleti, dipendenze rotte e vulnerabilità note del runtime.

Non committare segreti, `data/` o `logs/`. Lo startup rifiuta `.env`, credenziali
OAuth e token Drive presenti con mode diverso da `0600`; la directory dei log è
creata `0700` e il file `0600`. Lo startup crea schema e seed se il DB è vuoto.

Per autorizzare Drive, prima applicare `chmod 600 credentials_oauth.json`, quindi
eseguire `.venv/bin/python -m scripts.authorize_drive`. Lo script genera o aggiorna
`token_drive.json` a `0600`. `scripts/backup_env.sh` forza directory backup `0700`
e copie `0600` senza elencarne il contenuto.

## Controlli quotidiani

- `GET /health` verifica solo che il processo HTTP sia vivo.
- Controllare heartbeat Telegram, ultimo digest, backlog `approved/publishing` e feed con errori consecutivi.
- Un 200 su `/health` non garantisce che fetch, Telegram o Drive funzionino.

## Incidenti

### Digest assente

1. Verificare log attorno alle 07:00 senza condividere URL Telegram completi.
2. Verificare spazio disco, DB e connettività.
3. Controllare se esistono articoli della data: oggi questa condizione può nascondere un run parziale.
4. Prima di rilanciare manualmente, controllare la coda per evitare duplicati.

### Articolo bloccato in `publishing`

Il recovery startup lo riporta ad `approved`, ma lo slot originale può essere passato. Verificare prima se Telegram ha già ricevuto il post; poi ripianificare manualmente. Finché non esiste `telegram_message_id`, la garanzia è at-least-once e un duplicato resta possibile.

### Feed compromesso o anomalo

Disabilitarlo con `/feeddisable <id>`, controllare destinazioni/redirect e log, quindi rimuovere eventuali articoli non attendibili. Non riabilitare un feed che può risolvere verso IP privati.

Un errore `UnsafeFeedUrl` per egress policy, peer, redirect, timeout, 2 MiB/feed o quota 32 MiB/run è fail-closed e riguarda il feed indicato. Non aggirare il client sicuro né abilitare proxy ambientali: verificare DNS/URL fuori banda, correggere o disabilitare il feed e rieseguire solo nel ciclo successivo. Un burst di errori quota richiede riduzione/analisi dei feed, non aumento automatico del limite.

### Messaggio Telegram rifiutato

Il renderer invia HTML escapato e divide i messaggi senza spezzare tag o entity. Un URL non HTTP(S), privo di host o con credenziali viene mostrato come label non cliccabile. Se Telegram rifiuta comunque il payload, non ritentare automaticamente una pubblicazione dall'esito ambiguo: verificare prima il canale, quindi conservare il contenuto problematico come evidenza sanitizzata senza token o dati riservati.

### Token esposto

Revocare/ruotare presso Telegram o Google, sostituire il file con mode `0600`, cercare l'esposizione in history/log/backup e verificare accessi Drive. Cancellare il file locale non revoca il token.

## Backup e restore

Il job corrente carica copie SQLite su Drive, ma non applica retention né verifica restore. Prima di considerarlo un backup affidabile: definire RPO/RTO, usare snapshot SQLite consistente, limitare ACL, conservare un numero definito di copie e provare periodicamente il restore su un ambiente isolato.
