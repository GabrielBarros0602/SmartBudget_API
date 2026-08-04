# ADR-001: Layered architecture (router → service → repository)

- **Status:** Accepted
- **Date:** 2026-08-04
- **Deciders:** Gabriel Barros

## Context

SmartBudget API handles personal finance data: transactions, categories,
budgets and threshold alerts. Most of the interesting work is not I/O — it is
**rules**: deciding which category a transaction belongs to, aggregating a
month into a report, and deciding whether spending has crossed 80% or 100% of a
budget limit.

Constraints that shaped the decision:

- Single developer, part-time, targeting a working MVP in a few weeks.
- Business rules must be unit-testable **without** an HTTP client and **without**
  a live PostgreSQL instance, otherwise the test suite becomes slow and fragile.
- The stack is fixed: FastAPI + SQLAlchemy + PostgreSQL.
- The codebase is a portfolio piece: a reviewer should be able to open any file
  and immediately know what kind of logic is allowed to live there.

## Decision

Organise the application in four layers with a strictly one-directional
dependency flow:

```
HTTP request
    │
    ▼
router      app/api/         parse & validate input, call a service, shape the response
    │
    ▼
service     app/services/    ALL business rules live here
    │
    ▼
repository  app/repositories/  database access only, no rules
    │
    ▼
database    PostgreSQL
```

Two rules make this real rather than decorative:

1. **Business rules live only in the service layer.** A router that contains an
   `if` about money, and a repository that knows what "over budget" means, are
   both defects.
2. **Repositories are injected into services through FastAPI's `Depends`**, never
   instantiated inside a service. The service depends on the repository's
   interface, not on the fact that it happens to talk to PostgreSQL today.

## Alternatives considered

### Option A — Routers talk to SQLAlchemy directly (no layers)

- Pros: fastest to write; fewer files; common in FastAPI tutorials.
- Cons: budget-threshold logic ends up inside HTTP handlers, so testing it
  requires spinning up a client and a database; the same rule gets duplicated
  the moment a second entry point needs it (e.g. a scheduled alert job).
- Why not chosen: the alert rules are the part of this project worth showing to
  a reviewer. Burying them in route handlers hides the actual engineering.

### Option B — Layered architecture (chosen)

- Pros: rules are isolated and unit-testable with fakes; each directory has one
  obvious responsibility; it is the structure most back-end teams actually use,
  so it reads as familiar rather than exotic.
- Cons: more files and more indirection than the domain strictly needs today;
  risk of anemic services that only forward calls to repositories.
- Why chosen: the cost is a handful of extra modules; the benefit is that every
  business rule has exactly one home.

### Option C — Hexagonal architecture (ports & adapters)

- Pros: the domain becomes fully framework-agnostic; swapping FastAPI or
  SQLAlchemy would touch only adapters.
- Cons: explicit port interfaces, DTO mapping at every boundary, and a domain
  model separate from the ORM model — a large amount of ceremony for a domain
  with roughly five entities.
- Why not chosen: the flexibility it buys is not needed yet. Choosing it now
  would be architecture as decoration. See *Revisit triggers*.

## Consequences

### Positive

- Service tests run against in-memory fake repositories: fast, no Docker needed.
- The persistence implementation can change without touching business rules.
- Code review has an objective rule to check: "is there a business rule outside
  `app/services/`?"

### Negative

- More boilerplate per feature — a new entity touches four files instead of one.
- Real risk of pass-through services early on, while CRUD dominates. Accepted:
  budgets and alerts in S3 give the layer genuine substance.

### Neutral

- `app/models/` (SQLAlchemy) and `app/schemas/` (Pydantic) stay separate, so the
  public API contract can evolve independently of the database schema.

## Revisit triggers

Reopen this decision — in a **new** ADR, not by editing this one — if any of these happen:

- Business rules need to run outside an HTTP request (e.g. a scheduled job that
  re-evaluates budget alerts nightly), making the framework coupling costly.
- A second persistence implementation becomes real, not hypothetical.
- Services start needing to call each other in cycles, which layering cannot
  express cleanly.
