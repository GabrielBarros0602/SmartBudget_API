"""A user's spending or income category."""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Redundant in logic — id is already unique — but it is the target of
        # the composite foreign keys that keep owners consistent (ADR-003).
        UniqueConstraint("id", "user_id"),
        CheckConstraint("btrim(name) <> ''", name="name_not_blank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))


# Unique per user on the normalised name: "Food" and "food" are one category.
Index(
    "uq_categories_user_id_name_lower",
    Category.user_id,
    func.lower(Category.name),
    unique=True,
)
