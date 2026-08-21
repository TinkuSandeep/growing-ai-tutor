from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_login
from app.database import get_db
from app.models import QuizQuestion, Student
from app.schemas import AbacusRequest, QuizAnswer, TutorRequest
from app.services.abacus import represent, teaching_steps
from app.services.progress import record_attempt
from app.services.quiz import TOPICS, generate_question
from app.services.supervisor import recommend_next
from app.services.tutor import explain_for_child

router = APIRouter(prefix="/api", tags=["learning"], dependencies=[Depends(require_login)])


@router.get("/curriculum")
def curriculum():
    return TOPICS


@router.get("/quiz")
def quiz(subject: str, topic: str, difficulty: int = 1, db: Session = Depends(get_db)):
    try:
        generated = generate_question(subject, topic, difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    saved = QuizQuestion(
        subject=generated["subject"],
        topic=generated["topic"],
        prompt=generated["question"],
        correct_answer=generated["correct_answer"],
        difficulty=generated["difficulty"],
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return {
        "question_id": saved.id,
        "subject": saved.subject,
        "topic": saved.topic,
        "question": saved.prompt,
        "difficulty": saved.difficulty,
    }


@router.post("/quiz/answer")
def answer(payload: QuizAnswer, db: Session = Depends(get_db)):
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    question = db.get(QuizQuestion, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.answered_at is not None:
        raise HTTPException(status_code=409, detail="Question already answered")
    return record_attempt(db, student_id=payload.student_id, question=question, submitted_answer=payload.submitted_answer)


@router.post("/tutor")
def tutor(payload: TutorRequest, db: Session = Depends(get_db)):
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return explain_for_child(
        grade=student.grade,
        subject=payload.subject,
        topic=payload.topic,
        question=payload.question,
        language=payload.language or student.preferred_language,
    )


@router.get("/recommendation/{student_id}")
def recommendation(student_id: int, db: Session = Depends(get_db)):
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return recommend_next(db, student_id)


@router.post("/abacus")
def abacus(payload: AbacusRequest):
    return {**represent(payload.number), "steps": teaching_steps(payload.number)}
