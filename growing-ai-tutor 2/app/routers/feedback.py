from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.models import Feedback, Student
from app.schemas import FeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["feedback"], dependencies=[Depends(require_login)])


@router.post("")
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    if payload.student_id is not None and not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    row = Feedback(**payload.model_dump())
    db.add(row)
    db.commit()
    return {"ok": True, "message": "Thank you — your feedback will shape the next beta. 🙏"}


@router.get("/summary")
def feedback_summary(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Feedback.id))) or 0
    useful_yes = db.scalar(select(func.count(Feedback.id)).where(Feedback.useful_rating == "yes")) or 0
    regular_yes = db.scalar(select(func.count(Feedback.id)).where(Feedback.regular_use == "yes")) or 0
    language_rows = db.execute(
        select(Feedback.preferred_language, func.count(Feedback.id)).group_by(Feedback.preferred_language)
    ).all()
    pay_rows = db.execute(
        select(Feedback.willingness_to_pay, func.count(Feedback.id)).group_by(Feedback.willingness_to_pay)
    ).all()
    return {
        "responses": total,
        "useful_yes_pct": round(useful_yes / total * 100, 1) if total else 0,
        "regular_use_yes_pct": round(regular_yes / total * 100, 1) if total else 0,
        "language_preferences": dict(language_rows),
        "willingness_to_pay": dict(pay_rows),
    }
