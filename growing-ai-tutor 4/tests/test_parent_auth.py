from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Parent


def test_parent_register_logout_and_login():
    client = TestClient(app)
    email = "parent-auth-test@example.com"
    password = "safe-family-password"

    response = client.post(
        "/api/auth/register",
        json={
            "display_name": "Test Parent",
            "email": email,
            "password": password,
            "invite_code": "FAMILY-BETA",
        },
    )
    assert response.status_code == 201
    assert response.json()["parent"]["email"] == email

    with SessionLocal() as db:
        parent = db.scalar(select(Parent).where(Parent.email == email))
        assert parent is not None
        assert parent.password_hash != password

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/status").json()["authenticated"] is False

    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    assert client.get("/api/auth/status").json()["authenticated"] is True


def test_shared_invite_code_can_register_multiple_families():
    client = TestClient(app)
    for suffix in ("one", "two"):
        response = client.post("/api/auth/register", json={
            "display_name": f"Family {suffix}",
            "email": f"shared-code-{suffix}@example.com",
            "password": "safe-family-password",
            "invite_code": "FAMILY-BETA",
        })
        assert response.status_code == 201
        client.post("/api/auth/logout")
