"""Account that owns every other row."""

from sqlalchemy import BigInteger, Identity, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    # Present from the first migration so S3 never adds a NOT NULL column to a
    # populated table.
    password_hash: Mapped[str] = mapped_column(String(255))


# Uniqueness falls on the normalised address: Ana@x.com and ana@x.com are one account.
Index("uq_users_email_lower", func.lower(User.email), unique=True)
