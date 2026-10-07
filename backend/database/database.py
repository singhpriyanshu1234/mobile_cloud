"""SQLite engine + session handling (SQLAlchemy).

The rest of the app only talks to the database through `get_db`
and the service layer, so SQLite can later be swapped for
PostgreSQL by changing DATABASE_URL + one driver line.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.utils import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they register on Base.metadata, then create tables.
    from backend.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
