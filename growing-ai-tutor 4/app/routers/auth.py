import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Parent
from app.schemas import ParentLoginRequest, ParentRegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
password_hash = PasswordHash.recommended()


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    return value


def invite_use_digest(code: str, email: str) -> str:
    """Record a unique use without making a shared beta code single-use."""
    return hashlib.sha256(f"{code.strip()}|{email}".encode("utf-8")).hexdigest()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: ParentRegisterRequest, request: Request, db: Session = Depends(get_db)):
    invite = payload.invite_code.strip()
    if not any(secrets.compare_digest(invite, code) for code in settings.invite_codes):
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    email = normalize_email(payload.email)
    parent = Parent(
        display_name=payload.display_name.strip(),
        email=email,
        password_hash=password_hash.hash(payload.password),
        invite_code_hash=invite_use_digest(invite, email),
    )
    db.add(parent)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account already exists for this email") from exc
    db.refresh(parent)
    request.session.clear()
    request.session["parent_id"] = parent.id
    return {"ok": True, "parent": {"id": parent.id, "name": parent.display_name, "email": parent.email}}


@router.post("/login")
def login(payload: ParentLoginRequest, request: Request, db: Session = Depends(get_db)):
    parent = db.scalar(select(Parent).where(Parent.email == normalize_email(payload.email)))
    if not parent or not password_hash.verify(payload.password, parent.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    request.session.clear()
    request.session["parent_id"] = parent.id
    return {"ok": True, "parent": {"id": parent.id, "name": parent.display_name, "email": parent.email}}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/status")
def auth_status(request: Request, db: Session = Depends(get_db)):
    parent_id = request.session.get("parent_id")
    parent = db.get(Parent, int(parent_id)) if parent_id else None
    return {
        "authenticated": bool(parent),
        "parent": {"id": parent.id, "name": parent.display_name, "email": parent.email} if parent else None,
        "is_beta_owner": bool(parent and parent.email.lower() in settings.owner_emails),
    }
