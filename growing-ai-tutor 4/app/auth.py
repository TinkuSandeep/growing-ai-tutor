from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Parent, Student


def require_login(request: Request):
    parent_id = request.session.get("parent_id")
    if not parent_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
    return int(parent_id)


def require_beta_owner(parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    parent = db.get(Parent, parent_id)
    if not parent or parent.email.lower() not in get_settings().owner_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Beta owner access required")
    return parent


def owned_student(db: Session, student_id: int, parent_id: int) -> Student:
    student = db.scalar(select(Student).where(Student.id == student_id, Student.parent_id == parent_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
