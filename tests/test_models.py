"""The schema rules ADR-003 records, read from the DDL the models compile to.

These pin what the models declare. That PostgreSQL enforces it is proven in S1
block 4, against a migrated database.
"""

import pytest
from sqlalchemy.schema import CreateIndex, CreateTable

import app.models  # noqa: F401  registers every table on Base.metadata
from app.core.database import Base, engine

OWNED_TABLES = ["categories", "transactions", "budgets"]


def _ddl(table_name: str) -> str:
    table = Base.metadata.tables[table_name]
    # The application's own dialect, so the DDL is what the migration would emit.
    dialect = engine.dialect
    parts = [str(CreateTable(table).compile(dialect=dialect))]
    parts += [str(CreateIndex(index).compile(dialect=dialect)) for index in table.indexes]
    return "\n".join(parts)


@pytest.mark.parametrize("table_name", sorted(Base.metadata.tables))
def test_every_constraint_has_a_name(table_name: str) -> None:
    # The API matches violations by constraint name, so none may be left to
    # PostgreSQL to name.
    table = Base.metadata.tables[table_name]

    assert _ddl(table_name).count("CONSTRAINT ") == len(table.constraints)


@pytest.mark.parametrize(
    ("table_name", "column", "constraint"),
    [
        ("transactions", "amount", "ck_transactions_amount_positive"),
        ("budgets", "limit_amount", "ck_budgets_limit_amount_positive"),
    ],
)
def test_money_is_exact_and_positive(table_name: str, column: str, constraint: str) -> None:
    ddl = _ddl(table_name)

    assert f"{column} NUMERIC(12, 2) NOT NULL" in ddl
    assert f"CONSTRAINT {constraint} CHECK ({column} > 0)" in ddl


def test_kind_is_a_checked_varchar_not_an_enum() -> None:
    ddl = _ddl("transactions")

    assert "kind VARCHAR(16) NOT NULL" in ddl
    assert "CONSTRAINT ck_transactions_kind_valid CHECK (kind IN ('income', 'expense'))" in ddl


def test_a_category_with_transactions_cannot_be_deleted() -> None:
    ddl = _ddl("transactions")

    assert "category_id BIGINT NOT NULL" in ddl
    assert (
        "CONSTRAINT fk_transactions_category_id_user_id_categories "
        "FOREIGN KEY(category_id, user_id) REFERENCES categories (id, user_id) "
        "ON DELETE NO ACTION"
    ) in ddl


def test_a_budget_goes_with_its_category() -> None:
    assert (
        "CONSTRAINT fk_budgets_category_id_user_id_categories "
        "FOREIGN KEY(category_id, user_id) REFERENCES categories (id, user_id) "
        "ON DELETE CASCADE"
    ) in _ddl("budgets")


def test_categories_are_a_valid_target_for_the_composite_keys() -> None:
    assert "CONSTRAINT uq_categories_id_user_id UNIQUE (id, user_id)" in _ddl("categories")


@pytest.mark.parametrize("table_name", OWNED_TABLES)
def test_deleting_a_user_deletes_what_it_owns(table_name: str) -> None:
    assert (
        f"CONSTRAINT fk_{table_name}_user_id_users "
        "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE"
    ) in _ddl(table_name)


def test_one_budget_per_category_per_month() -> None:
    ddl = _ddl("budgets")

    assert (
        "CONSTRAINT uq_budgets_user_id_category_id_month UNIQUE (user_id, category_id, month)"
    ) in ddl
    assert "CONSTRAINT ck_budgets_month_first_day CHECK (EXTRACT(DAY FROM month) = 1)" in ddl


def test_uniqueness_falls_on_normalised_values() -> None:
    assert "CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email))" in _ddl("users")
    assert (
        "CREATE UNIQUE INDEX uq_categories_user_id_name_lower ON categories (user_id, lower(name))"
    ) in _ddl("categories")


def test_a_category_name_cannot_be_blank() -> None:
    assert "CONSTRAINT ck_categories_name_not_blank CHECK (btrim(name) <> '')" in _ddl("categories")


def test_the_monthly_report_has_its_index() -> None:
    assert (
        "CREATE INDEX ix_transactions_user_id_occurred_on ON transactions (user_id, occurred_on)"
    ) in _ddl("transactions")
