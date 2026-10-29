# ADR-003: Domain model — amount sign, ownership and deletion

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Gabriel Barros

## Context

Block 3 of S1 creates the first models: `User`, `Category`, `Transaction` and
`Budget`. Five choices shape their schema, and each becomes a data migration the
moment real rows exist. Two of them answer questions S2 had left open — *is a
zero amount valid?* and *can a category with transactions be deleted?* — because
the constraint that enforces the answer is created here, not in S2.

[ADR-002](ADR-002-data-modelling-foundations.md) already fixes the foundations:
money is `NUMERIC(12, 2)` handled as `Decimal`, transaction dates are `DATE`,
primary keys are `BIGINT` identity, and ownership must be enforced in the
repository layer.

Every constraint and index is named through the metadata naming convention, so
the API can recognise a violation **by constraint name from the driver's
diagnostics**, never by matching message text.

---

## Decision 1 — The amount is always positive; direction is a separate `kind`

```
amount NUMERIC(12, 2) NOT NULL  CHECK (amount > 0)
kind   VARCHAR        NOT NULL  CHECK (kind IN ('income', 'expense'))
```

The sign of a number never carries meaning. The monthly report sums by `kind`;
a budget compares against `expense` only.

### Alternative considered — signed amount

A negative amount is an expense, a positive one is income.

- Pros: one column fewer.
- Cons: `CHECK (amount <> 0)` cannot catch a sign entered the wrong way round,
  which is the likeliest data-entry error in the domain. Every aggregate has to
  filter by sign, and the meaning lives in a convention instead of a column.
- Why not chosen: the schema can enforce a positive number and a closed set of
  kinds; it cannot enforce that a sign was meant.

### Consequences

- **A zero amount is invalid**, enforced by the schema. This closes that
  question for S2.

---

## Decision 2 — `kind` is a `VARCHAR` with a `CHECK`, not a PostgreSQL `ENUM`

### Alternative considered — `ENUM` type

- Pros: the set of values is a named type.
- Cons: a value cannot be removed or renamed without recreating the type and
  rewriting every column that uses it, and adding one carries restrictions
  inside a migration's transaction.
- Why not chosen: changing a `CHECK` is a plain constraint swap in one
  migration, with the same guarantee on every write.

---

## Decision 3 — A category with transactions cannot be deleted

`transactions.category_id` is `NOT NULL`, and its foreign key is declared
`ON DELETE NO ACTION` explicitly. The API translates the violation into `409`,
matched by the constraint's name.

No money record disappears or changes category as a side effect of deleting
something else.

### Why `NO ACTION` and not `RESTRICT`

Both refuse the delete. `RESTRICT` is checked immediately, row by row;
`NO ACTION` is checked at the end of the statement. Deleting a user cascades to
its categories and its transactions in one statement, and with `RESTRICT` that
cascade can fail depending on the order the rows are removed in. `NO ACTION`
checks once both are gone.

### Alternatives considered

#### `ON DELETE SET NULL`

- Pros: deleting a category always succeeds; its transactions become
  "uncategorised" in the report.
- Cons: `category_id` becomes nullable, and history is reclassified silently.
- Why not chosen: a past month's report would change without anyone touching a
  transaction.

#### `ON DELETE CASCADE`

- Rejected outright: it deletes money records.

### Consequences

- Removing a category means moving its transactions first. S2 can offer that as
  an explicit operation.

---

## Decision 4 — Ownership across tables is enforced by the schema

`transactions` and `budgets` carry their own `user_id`, and reach their
category through a composite foreign key:

```
FOREIGN KEY (category_id, user_id) REFERENCES categories (id, user_id)
```

which requires `UNIQUE (id, user_id)` on `categories`.

The database refuses a transaction of user A that points to a category of
user B, whatever code path writes it. The direct `user_id` also lets the
owner-scoped repository base planned for S3 filter every table without a join.

### Alternative considered — `category_id` only, owner derived by join

- Pros: fewer columns, no redundant unique constraint.
- Cons: isolation between users would depend on code alone, and every scoped
  query on `transactions` would need a join to find its owner.
- Why not chosen: ADR-002 already makes ownership checks the condition its
  sequential keys depend on; the schema should hold the part of that it can.

### Consequences

- `UNIQUE (id, user_id)` adds nothing logically — `id` is already unique — but
  PostgreSQL requires a unique constraint on the referenced columns.
- On delete, the composite key follows Decision 3 for transactions
  (`NO ACTION`) and cascades for budgets, which mean nothing without their
  category.

---

## Decision 5 — A budget is one row per category per month

```
month        DATE           NOT NULL  CHECK (EXTRACT(DAY FROM month) = 1)
limit_amount NUMERIC(12, 2) NOT NULL  CHECK (limit_amount > 0)
UNIQUE (user_id, category_id, month)
```

Changing November's limit does not rewrite how October was evaluated, so the S3
alerts judge each month against the limit that applied to it. `month` as the
first day of the month keeps every filter a plain `DATE` range, consistent with
ADR-002.

### Alternative considered — one standing limit per category

- Pros: simpler; set once, applies every month.
- Cons: any change applies retroactively to every month already evaluated.
- Why not chosen: it makes past results unstable, which is what a budget
  history exists to avoid.

### Consequences

- A budget has to exist for each month it applies to. S3 can offer copying the
  previous month's limits.

---

## Consequences

### Positive

- The rules hold for every write path — the API, a manual `INSERT`, the CSV
  import planned as stretch.
- Named constraints give the API stable handles to translate into domain
  errors.

### Negative

- More constraints to migrate, and block 4 has to test each one against
  PostgreSQL; checking the metadata alone does not prove them.

### Neutral

- *Can a transaction have a future date?* stays an S2 service rule. A `CHECK`
  depending on `current_date` is not immutable, and PostgreSQL assumes every
  `CHECK` condition is.

## Revisit triggers

- Transfers between accounts or refunds become concepts of their own — the set
  of kinds grows, or signed amounts become natural.
- Recurring budgets are requested and one row per month proves a burden.
- Categories shared between users (a household) are requested — the ownership
  model changes.
