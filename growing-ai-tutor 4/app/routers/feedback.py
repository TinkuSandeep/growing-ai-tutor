import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import owned_student, require_beta_owner, require_login
from app.database import get_db
from app.models import Feedback, Parent, Student
from app.schemas import FeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["feedback"], dependencies=[Depends(require_login)])


@router.post("")
def submit_feedback(payload: FeedbackCreate, parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    if payload.student_id is not None:
        owned_student(db, payload.student_id, parent_id)
    row = Feedback(**payload.model_dump())
    db.add(row)
    db.commit()
    return {"ok": True, "message": "Thank you — your feedback will shape the next beta. 🙏"}


@router.get("/summary")
def feedback_summary(parent_id: int = Depends(require_login), db: Session = Depends(get_db)):
    family_feedback = select(Feedback.id).join(Student).where(Student.parent_id == parent_id)
    total = db.scalar(select(func.count()).select_from(family_feedback.subquery())) or 0
    useful_yes = db.scalar(select(func.count(Feedback.id)).join(Student).where(Student.parent_id == parent_id, Feedback.useful_rating == "yes")) or 0
    regular_yes = db.scalar(select(func.count(Feedback.id)).join(Student).where(Student.parent_id == parent_id, Feedback.regular_use == "yes")) or 0
    language_rows = db.execute(
        select(Feedback.preferred_language, func.count(Feedback.id)).join(Student).where(Student.parent_id == parent_id).group_by(Feedback.preferred_language)
    ).all()
    pay_rows = db.execute(
        select(Feedback.willingness_to_pay, func.count(Feedback.id)).join(Student).where(Student.parent_id == parent_id).group_by(Feedback.willingness_to_pay)
    ).all()
    return {
        "responses": total,
        "useful_yes_pct": round(useful_yes / total * 100, 1) if total else 0,
        "regular_use_yes_pct": round(regular_yes / total * 100, 1) if total else 0,
        "language_preferences": dict(language_rows),
        "willingness_to_pay": dict(pay_rows),
    }


@router.get("/owner/summary")
def owner_feedback_summary(_owner: Parent = Depends(require_beta_owner), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Feedback.id))) or 0
    families = db.scalar(select(func.count(func.distinct(Student.parent_id))).join(Feedback)) or 0
    useful_yes = db.scalar(select(func.count(Feedback.id)).where(Feedback.useful_rating == "yes")) or 0
    regular_yes = db.scalar(select(func.count(Feedback.id)).where(Feedback.regular_use == "yes")) or 0
    return {
        "responses": total,
        "families": families,
        "useful_yes_pct": round(useful_yes / total * 100, 1) if total else 0,
        "regular_use_yes_pct": round(regular_yes / total * 100, 1) if total else 0,
    }


@router.get("/owner/export.csv")
def export_feedback(_owner: Parent = Depends(require_beta_owner), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Feedback, Parent.email, Student.display_name)
        .outerjoin(Student, Feedback.student_id == Student.id)
        .outerjoin(Parent, Student.parent_id == Parent.id)
        .order_by(Feedback.created_at.desc())
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["submitted_at", "parent_email", "student", "useful", "difficulty", "language", "regular_use", "pay_choice", "requested_features", "comments"])
    for feedback, email, student_name in rows:
        writer.writerow([feedback.created_at.isoformat(), email or "", student_name or "", feedback.useful_rating, feedback.difficulty_rating, feedback.preferred_language, feedback.regular_use, feedback.willingness_to_pay, feedback.requested_features, feedback.comments])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=family-beta-feedback.csv"})
