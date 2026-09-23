from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL


engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    """Shared declarative base for application models and Alembic metadata."""


SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session and always close it afterwards."""
    with SessionLocal() as session:
        yield session
