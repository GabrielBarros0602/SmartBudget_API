# Architecture Decision Records

Every non-trivial architectural decision in this project is recorded here, so
the *reasoning* survives even when the code changes.

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](ADR-001-layered-architecture.md) | Layered architecture (router → service → repository) | Accepted | 2026-08-04 |
| [ADR-002](ADR-002-data-modelling-foundations.md) | Data modelling foundations — money, dates and primary keys | Accepted | 2026-08-05 |

Use [ADR-000-template.md](ADR-000-template.md) as the starting point for a new record.

## Conventions

- One file per decision, numbered sequentially, never renumbered.
- ADRs are immutable once accepted. To change a decision, write a new ADR that
  supersedes the old one and update the old one's status to `Superseded by ADR-XXX`.
- Statuses: `Proposed` → `Accepted` → `Superseded` / `Deprecated`.
