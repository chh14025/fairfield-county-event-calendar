from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _micro_migrations() -> None:
    """Additive column migrations for existing databases. create_all only creates
    missing tables — it never ALTERs. Replace with Alembic when schema churn grows."""
    from sqlalchemy import text

    stmts = [
        "ALTER TABLE events ADD COLUMN rejection_reason TEXT",
    ]
    with engine.connect() as conn:
        for stmt in stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:  # noqa: BLE001 — column already exists
                conn.rollback()


def init_db() -> None:
    """Dev convenience; Alembic migrations replace this before prod (SPEC 12)."""
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
    _micro_migrations()
