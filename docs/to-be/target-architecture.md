# Target architecture — modular monolith

```text
src/dritara/
  bootstrap/       settings, logging, dependency wiring
  domain/          article, editorial policy, publication state
  application/     digest, review, publish, recovery use cases + ports
  adapters/
    db/            SQLModel/Alembic/repositories
    rss/           HTTP parser and network policy
    telegram/      client, bot controller, renderers
    drive/         export and backup
    health/        live/ready
    scheduling/    APScheduler registration only
  entrypoints/     service and maintenance commands
```

Regola: `entrypoints/adapters → application → domain`. Domain non importa SQLModel, HTTPX, APScheduler, Telegram o Drive. Application usa Protocol/port e DTO propri; nessun framework DI richiesto.

## Migrazione incrementale

1. settings/bootstrap e import safety;
2. funzioni pure: queue policy, clock, rendering sicuro;
3. repository e state machine nuovi accanto al legacy;
4. dual-write/shadow comparison;
5. feature flag per reader/worker nuovi;
6. controller bot e scheduler sottili;
7. spostamento fisico finale con shim dei vecchi import per una release.

Non spostare tutti i moduli insieme a schema e comportamento. Ogni seam deve essere coperto da characterization test.

Esecuzione: M01 crea bootstrap/settings; M02–M04 stabilizzano repository e state machine; M05.01–M05.04 applicano dependency fitness rule, use case, port e package layout. Il gate M05 verifica che il diagramma descriva l'AS-IS prima di considerare conclusa la migrazione.

## Non obiettivi attuali

Microservizi, Postgres, async ORM, multi-tenancy e framework DI. Vanno rivalutati solo con più editor/istanze, HA richiesta o contesa misurata.
