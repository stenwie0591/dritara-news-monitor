# Changelog

## Unreleased

### Added

- Project brain per AS-IS, TO-BE, sicurezza, prodotto, operazioni e handoff AI.
- CI, dev dependencies e test di regressione/sicurezza URL/configurazione.
- Safe feed fetch con validazione DNS/redirect e limiti payload.
- Configurazione runtime tipizzata e import-safe.
- Dritara Evidence-Gated Delivery Framework, DoD risk-based e template macro/micro/gate.
- Roadmap prodotto/tecnica M00–M08 con micro-task e Definition of Done specifiche.
- Configurazione runtime iniettata dal composition root, validazione aggregata e redazione centralizzata dei token.

### Changed

- Startup inizializza il DB e valida la configurazione.
- Slot pubblicazione ordinati 09/13/18/22.
- Metadata scoring salvati come JSON; lettura legacy compatibile.
- `/feedadd`, analisi keyword, permessi segreti e CSV export corretti.

### Security

- Mitigazioni SSRF, CSV formula injection e file secret mode 0600.
- Autorizzazione Telegram vincolata a user ID, chat configurata e chat privata.
- Rendering Telegram centralizzato in HTML con escaping fail-safe, filtro control/bidi, link HTTP(S) validati e contract/abuse test.
- Fetch RSS con DNS pinning, peer validation, client no-proxy/no-retry, redirect manuali, streaming cap, quota per run e field limits.

### Known limitations

- State machine anti-duplicato, migrazioni Alembic e nuova UX editoriale non sono ancora attive.
