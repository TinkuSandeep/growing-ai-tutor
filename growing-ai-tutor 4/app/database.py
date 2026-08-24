from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


def resolved_database_url() -> str:
    """Return a SQLAlchemy-compatible database URL."""
    url = settings.database_url
    # Marketplace providers may expose the conventional postgres:// URL. Make the
    # psycopg 3 driver explicit so SQLAlchemy never falls back to legacy psycopg2.
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = resolved_database_url()

# SQLite does not create a missing parent directory.  A clean checkout uses
# ``./data/tutor.db`` while Vercel's temporary fallback uses ``/tmp``; ensure
# either location exists before SQLAlchemy opens the database.
if DATABASE_URL.startswith("sqlite:///") and DATABASE_URL != "sqlite:///:memory:":
    sqlite_path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_options = {"connect_args": connect_args, "pool_pre_ping": True}
if DATABASE_URL.startswith("postgresql"):
    # Keep the per-function pool small; Neon/Vercel supplies a pooled endpoint.
    engine_options.update({"pool_size": 2, "max_overflow": 3, "pool_recycle": 300})
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
