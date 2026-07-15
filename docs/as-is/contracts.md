# External contracts — AS-IS

## Telegram admin

Polling `getUpdates`, soli messaggi. Comandi e callback richiedono insieme `from.id == TELEGRAM_ADMIN_USER_ID`, chat configurata e chat privata. Comandi pubblici nel README. Posizioni sono riferite al digest corrente e non versionate.

## Telegram community

`sendMessage` con HTML costruito dal renderer centralizzato e thread ID. Testo e attributi sono escapati, control/bidi rimossi, link limitati a HTTP(S) senza credenziali e messaggi divisi conservativamente entro il limite Telegram. Successo produce `message_id`, che oggi non è persistito. Timeout/errore ambiguo non è distinguibile da mancato invio e non introduce retry automatici.

## RSS

Input HTTP(S) pubblico. Ogni connect risolve solo IP globali, connette direttamente all'IP validato e richiede un peer coincidente; proxy ambientali, retry, keepalive e redirect automatici sono disabilitati. Ogni redirect è rivalidato. Limiti: 15 secondi sull'intera chain, tre redirect, 2 MiB/feed letti in streaming, 32 MiB/run, 200 entry/feed, titolo 500, URL articolo 2048 ed excerpt 500 caratteri. RSS resta input non attendibile.

## Google Drive

OAuth `drive.file`, token locale `token_drive.json`. Crea/aggiorna CSV giornaliero e crea backup SQLite settimanale nella folder configurata. API Google è sincrona.

## HTTP

`GET /health` su `0.0.0.0:8088` restituisce testo `OK`/200. È sola liveness.

## Scheduler

Europe/Rome: digest 07:00; heartbeat 07:05; cleanup domenica 02:00; backup 02:30; publish 09/13/18/22. Questi valori sono nel codice, non in `config/settings.yaml`.
