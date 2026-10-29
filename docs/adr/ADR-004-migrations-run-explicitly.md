# ADR-004: Migrations run as an explicit step, never on start

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Gabriel Barros

## Context

S1 block 4 creates the first Alembic migration. Before it exists, the project
has to decide what triggers `alembic upgrade head`, because that choice shapes
the S4 `Dockerfile`, the deploy steps and the README.

Two facts constrain it:

- The liveness probe exists so an orchestrator can restart an unhealthy
  container. A restart is routine and automatic; nobody reviews it.
- A deploy may run more than one replica of the API, and every replica starts
  the same way.

## Decision

Migrations run only as a deliberate, separate step — `alembic upgrade head` —
and never as part of starting the application or its container.

- **Development:** run by hand, after creating the database and after every
  pull that brings a new migration.
- **CI:** a step before the tests, followed by the reversibility check
  (`downgrade base`, then `upgrade head`).
- **Deploy (S4):** a one-off command run before the new version is rolled out.

## Alternatives considered

### Option B — the container entrypoint runs `upgrade head` before uvicorn

- Pros: one command brings up a correct schema; nothing to remember.
- Cons: every restart can change the schema, including one the liveness probe
  asked for. Two replicas starting together race for the same migration. A
  migration that fails leaves the container in a restart loop, retrying a DDL
  change on every attempt.
- Why not chosen: it turns a routine, unreviewed event into a schema change.

### Option C — the application migrates itself in its lifespan hook

- Pros: no separate step anywhere.
- Cons: everything wrong with Option B, plus the application's database role
  needs DDL privileges for its whole lifetime.
- Why not chosen: the same coupling, with a wider permission.

## Consequences

### Positive

- A restart never mutates the schema; a failed migration is a failed command,
  seen and handled by whoever ran it.
- The role the application connects with does not need DDL privileges, which
  lets S4 split a migration role from a runtime role if it wants to.

### Negative

- One more step to remember locally. The README states it next to
  `docker compose up`, and starting the API on a stale schema fails on the
  first query that touches a missing column rather than silently.

### Neutral

- `/health/ready` checks connectivity, not schema version. A schema-version
  check in readiness is possible later, but would be its own decision.

## Revisit triggers

- The deploy target offers a release phase or a pre-deploy job that runs once
  per rollout — the explicit step moves there, unchanged in nature.
- Zero-downtime deploys are required — migrations then need an expand and
  contract discipline, which is a new decision on top of this one.
