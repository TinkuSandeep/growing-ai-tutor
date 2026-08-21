from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.models import Attempt, Progress, Student

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(require_login)])


@router.get("/{student_id}")
def dashboard(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    total = db.scalar(select(func.count(Attempt.id)).where(Attempt.student_id == student_id)) or 0
    correct = db.scalar(
        select(func.count(Attempt.id)).where(Attempt.student_id == student_id, Attempt.is_correct == 1)
    ) or 0
    progress = list(
        db.scalars(
            select(Progress).where(Progress.student_id == student_id).order_by(Progress.mastery.asc())
        ).all()
    )

    return {
        "student": {"id": student.id, "name": student.display_name, "grade": student.grade},
        "summary": {
            "questions": total,
            "correct": correct,
            "accuracy": round((correct / total * 100), 1) if total else 0.0,
        },
        "topics": [
            {
                "subject": p.subject,
                "topic": p.topic,
                "attempted": p.attempted,
                "correct": p.correct,
                "mastery": p.mastery,
                "difficulty": p.difficulty,
            }
            for p in progress
        ],
    }
