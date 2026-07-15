# Deployment

Il deploy riproducibile ARM64 e il rollback sono deliverable M05.07 e requisito del gate M05.

## AS-IS

Target dichiarato Raspberry Pi Debian 12/ARM64, ma il repository non contiene ancora un service systemd o una configurazione container funzionante. I precedenti placeholder Docker vuoti sono stati rimossi per non simulare un deploy supportato.

## Target consigliato

Systemd nativo prima scelta: singolo processo, `WorkingDirectory`, utente dedicato senza shell, `EnvironmentFile` mode 0600, restart controllato, filesystem protection e egress firewall. SQLite e token restano su path persistenti con ownership dedicata.

### Egress target

Il client RSS applicativo ignora proxy ambientali e permette soltanto HTTP(S) verso peer IP globali risolti e pinned. Il firewall host, da provare nel deliverable M05.07 senza applicarlo implicitamente a workstation o Raspberry, deve negare loopback, private, carrier-grade NAT, link-local, multicast e range riservati IPv4/IPv6; permettere DNS esclusivamente verso i resolver amministrati e le uscite pubbliche necessarie a RSS, Telegram e Google Drive. Le regole concrete dipendono dalla rete del deploy e richiedono smoke test, console di recovery e rollback prima dell'attivazione.

## Release checklist target

Backup/restore verificato; migration esplicita; `make check`; config validate; restart; `/live` e `/ready`; smoke bot admin; scheduler jobs; backlog unknown; log senza segreti. Rollback = binario/config precedente e, per schema non additive, restore snapshot.

Decidere in backlog se supportare ufficialmente systemd, container o entrambi; non pubblicare istruzioni finché non sono verificate su ARM64.
