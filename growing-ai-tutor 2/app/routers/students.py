from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentLanguageUpdate, StudentOut

router = APIRouter(prefix="/api/students", tags=["students"], dependencies=[Depends(require_login)])


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return list(db.scalars(select(Student).order_by(Student.id)).all())


@router.post("", response_model=StudentOut)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(
        display_name=payload.display_name.strip(),
        grade=payload.grade,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.patch("/{student_id}/language", response_model=StudentOut)
def update_language(student_id: int, payload: StudentLanguageUpdate, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.preferred_language = payload.preferred_language
    db.commit()
    db.refresh(student)
    return student
