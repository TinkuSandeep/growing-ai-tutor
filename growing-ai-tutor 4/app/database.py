from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


def resolved_database_url() -> str:
    """Return the configured DB URL, using /tmp for Vercel-style prod SQLite fallback.

    The /tmp SQLite fallback is intentionally best-effort and non-persistent. For a
    real beta deployment set DATABASE_URL to PostgreSQL in Vercel.
    """
    url = settings.database_url
    if settings.is_prod and url == "sqlite:///./data/tutor.db":
        return "sqlite:////tmp/growing-ai-tutor.db"
    return url


DATABASE_URL = resolved_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
