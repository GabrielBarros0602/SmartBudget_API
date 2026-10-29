"""Alembic environment. Migrations run as an explicit step, never on start (ADR-004)."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  registers every table on Base.metadata
from app.core.config import get_settings
from app.core.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    # Settings by default; the test suite sets sqlalchemy.url to point Alembic
    # at its own database instead.
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Emit the migration as SQL (`alembic upgrade head --sql`) without connecting."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
