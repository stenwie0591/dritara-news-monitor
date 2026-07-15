# Risk register

| ID | Rischio | P/I | Mitigazione e trigger | Owner | Task | Stato |
|---|---|---|---|---|---|---|
| R-001 | duplicazione dopo esito Telegram ambiguo | H/H | stato `delivery_unknown`, zero retry, riconciliazione | product/tech | M03 | open |
| R-002 | corruzione/perdita durante migrazione DB legacy | M/H | backup API, checksum, dry-run copia, restore | tech/ops | M02 | open |
| R-003 | SSRF/DNS rebinding da feed amministrato | M/H | connect DNS-pinned, peer/hop validati, client no-proxy e cap/timeout/quota; firewall host al deploy | security | M01/M05.07 | mitigated/application-verified |
| R-004 | documentazione diverge dal runtime | M/M | DoD, docs check e gate review | maintainer | M00 | open |
| R-005 | refactoring big-bang interrompe servizio | M/H | characterization, seam, shim, feature flag | tech | M05 | open |
| R-006 | ranking/AI riduce pluralità territoriale | M/H | baseline, coverage audit, shadow mode, human approval | product | M06/M07 | open |

Probabilità/impatto (`P/I`): low, medium, high. Ogni rischio emerso riceve owner, task o accettazione esplicita; la review di macro aggiorna questo registro.
