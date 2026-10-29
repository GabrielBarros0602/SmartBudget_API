"""SQLAlchemy ORM models (database shape). Added in S1.

Importing this package registers every table on Base.metadata, which is what
Alembic compares against the database.
"""

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User

__all__ = ["Budget", "Category", "Transaction", "User"]
