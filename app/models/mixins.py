"""Columns every table carries."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Audit instants, stored as TIMESTAMPTZ in UTC (ADR-002)."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # shortcut: onupdate runs only for writes through the ORM, so a raw SQL
    # UPDATE leaves this stale; move it to a trigger if anything else writes.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
