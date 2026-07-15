# Threat model

## Asset

Token Telegram/OAuth, identità chat, integrità editoriale, storico decisioni, DB, disponibilità Raspberry, reputazione community e backup Drive.

## Trust boundaries

```text
Internet/RSS → safe fetch/parser → application/DB
Telegram user → bot auth/controller → use case
application → Telegram API/community
application → OAuth token → Google Drive
operator/AI agent → filesystem/repo/DB
```

## Minacce e controlli

| Minaccia | Stato | Controllo / gap |
|---|---|---|
| SSRF/redirect/DNS | mitigata | connect DNS-pinned, peer coincidente, no proxy/retry/auto-redirect, ogni hop rivalidato; firewall host resta defense-in-depth deploy |
| RSS memory/disk DoS | mitigata | timeout chain, streaming 2 MiB/feed, 32 MiB/run, 200 entry e field limits |
| Markdown/phishing/bidi | mitigata | renderer HTML unico, escaping testo/attributi, filtro control/bidi, link HTTP(S) senza credenziali, limiti e abuse test |
| CSV formula | mitigata | sanitizer testato |
| admin impersonation | mitigata | user ID + chat ID + chat privata; policy comune messaggi/callback e negative test |
| duplicate publish | aperta critica | barrier parziale; target unknown reconciliation |
| secret disclosure/log | mitigata | bootstrap fail-closed su file non `0600`/symlink, writer OAuth `0600`, log `0700`/`0600`, SecretStr e redazione pre-sink testata |
| DB corruption/schema drift | aperta | backup+Alembic+FK/WAL/preflight |
| malicious AI/RSS prompt | target | dati delimitati, structured output, no tools |
| supply chain | mitigata base | lock runtime/dev transitivi con hash, clean install e audit CI bloccante; SBOM/update automation restano M05.06 |
| backup over-retention | aperta | lifecycle, ACL audit, restore, encryption decision |

## Data classification

- Restricted: token, OAuth refresh/client secret.
- Confidential: chat/user IDs, DB decisioni, business metrics, logs operativi.
- Internal: feed config, scoring policy, audit/report.
- Public-derived: titoli, URL ed excerpt RSS; restano input non attendibili e soggetti a copyright.

## Security acceptance

Nessun segreto nel Git/diff/log; failure-safe su auth; egress deny private/link-local; provider errors redatti; dependency audit CI; incident playbook con revoca credenziali.

## Tracciabilità roadmap

M01 chiude trust boundary/config/auth/rendering/rete; M02 tratta integrità e schema; M03 previene duplicati e ambiguità; M05 copre supply chain/deploy; M07 valuta AI/prompt injection. Ogni gate riesamina minacce, controlli, rischio residuo e nuove superfici; i rischi correnti sono nel [risk register](../governance/risk-register.md).
