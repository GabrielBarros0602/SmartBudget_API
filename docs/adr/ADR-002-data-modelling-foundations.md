# ADR-002: Data modelling foundations — money, dates and primary keys

- **Status:** Accepted
- **Date:** 2026-08-05
- **Deciders:** Gabriel Barros

## Context

S1 introduces the first database schema. Three choices have to be made before
the first migration runs, because all three become expensive to reverse the
moment real rows exist: reversing them stops being a code change and becomes a
data migration.

They are grouped into one ADR because they are the same kind of decision —
foundations of the physical model — and because each one constrains the others.

The domain is personal finance in Brazil: values in BRL, transactions dated by
day, monthly aggregation, and budget limits evaluated as percentages.

---

## Decision 1 — Money is stored as `NUMERIC(12, 2)` and handled as `Decimal`

Every monetary column is `NUMERIC(12, 2)` in PostgreSQL, mapped to Python's
`decimal.Decimal`. `float` is forbidden anywhere in the path.

`12, 2` allows values up to `9,999,999,999.99` — far beyond any realistic
personal balance, while keeping the column narrow.

### Why not floating point

`float` is binary floating point: it cannot represent `0.1` exactly.

```python
>>> 0.1 + 0.2 == 0.3
False
>>> Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
True
```

The error is tiny per operation and **accumulates under aggregation** — which is
precisely what the monthly report does. A report that is off by cents is a
report nobody trusts, and in financial software that is disqualifying.

### Alternative considered — integer cents in `BIGINT`

Store `105000` to mean `R$ 1.050,00`.

- Pros: exact, fast, unambiguous in JSON, no decimal library needed.
- Cons: every boundary — API in, API out, report, budget threshold — needs a
  conversion. **A conversion bug is silent:** it produces a value that is wrong
  by a factor of 100 and raises nothing. Rows are also unreadable when
  inspecting the database directly during debugging.
- Why not chosen: `NUMERIC` is exact too, so the conversion layer buys only
  speed — irrelevant at this scale — while adding a class of silent, severe bug.

### Consequences

- **`Decimal` must always be built from a string or an integer, never a float.**
  `Decimal(0.1)` inherits the float's error before the decimal type can help;
  `Decimal("0.1")` is exact. This is the single most likely mistake in the
  codebase and belongs in code review.
- **Money is serialised as a JSON string, not a number.** Pydantic v2 does this
  by default and the default is kept:

  ```json
  { "amount": "1050.00" }
  ```

  A JSON number would be parsed as a float by most clients, reintroducing at the
  edge exactly the imprecision `NUMERIC` exists to prevent. The API contract
  documents amounts as decimal strings.
- Percentage arithmetic for the 80% / 100% budget thresholds stays exact, with
  rounding made explicit through `Decimal.quantize` where it is needed.

---

## Decision 2 — Transaction dates are `DATE`; audit timestamps are `TIMESTAMPTZ` in UTC

These are two different questions and they get two different types.

| Column | Type | Rationale |
|---|---|---|
| when the transaction happened | `DATE` | a purchase on 31 July is a July purchase, in every timezone |
| `created_at`, `updated_at` | `TIMESTAMPTZ` (UTC) | the exact instant matters and must be globally comparable |

### Why not `TIMESTAMPTZ` for the transaction date too

It looks more precise and is a common default. It also introduces a bug that is
hard to see and easy to ship:

> A transaction entered at 23:30 on 31 July in São Paulo (UTC−3) is stored as
> 02:30 on 1 August UTC. A monthly report grouping by UTC month drops it out of
> July — the month the user actually spent the money in.

The transaction date is a *calendar fact*, not an instant. A calendar fact has
no timezone, so giving it one only creates a conversion that can be done wrong.

`created_at` is the opposite: a real instant, where UTC is the correct and
standard storage, converted to local time only for display.

### Consequences

- Monthly aggregation is a plain `DATE` range filter with no timezone logic.
- The API accepts and returns transaction dates as `YYYY-MM-DD`.
- If the product ever needs the exact time of a transaction — for example to
  import a PIX statement with timestamps — a separate nullable `TIMESTAMPTZ`
  column is added rather than changing the type of the existing one.

---

## Decision 3 — Primary keys are `BIGINT`, generated as identity

Surrogate keys, `GENERATED ALWAYS AS IDENTITY`, one per table.

### Alternative considered — UUID

PostgreSQL 18 ships `uuidv7()`, which is time-ordered and therefore avoids the
index fragmentation that made UUIDv4 a poor primary key.

- Pros: identifiers are not guessable and do not reveal how many rows exist —
  `/transactions/42` tells an observer the system has at least 42 transactions.
- Cons: 16 bytes instead of 8, wider indexes, and URLs and debugging sessions
  become noticeably harder to read.
- Why not chosen: enumerable IDs are only a vulnerability when authorisation is
  missing. Every query in S3 must filter by owner regardless, and once it does,
  guessing `/transactions/43` returns `404` rather than someone else's data.
  UUID would make the attack more tedious, not impossible — it is obfuscation
  standing in for the access control that has to exist either way.

### Consequences

- Simple, readable identifiers and compact indexes.
- **The security of this choice is entirely dependent on ownership checks.** The
  filter by `user_id` must live in the repository layer, not be remembered
  endpoint by endpoint. This is recorded as a hard requirement for S3.
- If the API is ever exposed publicly to untrusted consumers, revisit — an
  external ID column alongside the internal key is the usual migration path, and
  is far cheaper than changing the primary key itself.

---

## Revisit triggers

Open a new ADR if any of these become true:

- Multi-currency support is added — `NUMERIC(12, 2)` assumes two decimal places,
  which not every currency uses.
- Transaction *times*, not just dates, become part of the domain.
- The API is exposed to untrusted third parties, making sequential IDs an
  information leak that ownership checks alone do not address.
