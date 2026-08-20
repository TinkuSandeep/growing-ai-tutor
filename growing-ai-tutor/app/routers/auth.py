import secrets

from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    ok = secrets.compare_digest(payload.password, settings.app_password)
    if not ok:
        return {"ok": False}
    request.session["authenticated"] = True
    return {"ok": True}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/status")
def status(request: Request):
    return {"authenticated": bool(request.session.get("authenticated"))}
