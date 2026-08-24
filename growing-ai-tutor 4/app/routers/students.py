from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import owned_student, require_login
from app.database import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentLanguageUpdate, StudentOut

router = APIRouter(prefix="/api/students", tags=["students"], dependencies=[Depends(require_login)])


@router.get("", response_model=list[StudentOut])
def list_students(parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    return list(db.scalars(select(Student).where(Student.parent_id == parent_id).order_by(Student.id)).all())


@router.post("", response_model=StudentOut)
def create_student(payload: StudentCreate, parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    student = Student(
        parent_id=parent_id,
        display_name=payload.display_name.strip(),
        grade=payload.grade,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}/language", response_model=StudentOut)
def update_language(student_id: int, payload: StudentLanguageUpdate, parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    student = owned_student(db, student_id, parent_id)
    student.preferred_language = payload.preferred_language
    db.commit()
    db.refresh(student)
    return student
