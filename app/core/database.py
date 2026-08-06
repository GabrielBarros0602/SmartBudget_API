"""Database engine, session factory and the declarative Base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class every ORM model inherits from.

    Collects table definitions in Base.metadata, which is what Alembic
    reads to generate migrations.
    """


engine = create_engine(get_settings().database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a session for one request, and close it afterwards.

    The finally block runs even if the endpoint raises, so the
    connection always returns to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
