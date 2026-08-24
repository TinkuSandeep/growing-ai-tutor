from app.database import resolved_database_url


def test_postgres_url_uses_psycopg3(monkeypatch):
    from app import database

    monkeypatch.setattr(database.settings, "database_url", "postgres://user:pass@host/db")
    assert resolved_database_url() == "postgresql+psycopg://user:pass@host/db"
