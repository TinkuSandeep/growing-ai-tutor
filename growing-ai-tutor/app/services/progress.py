from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Progress, QuizQuestion
from app.services.quiz import is_correct


def record_attempt(db: Session, *, student_id: int, question: QuizQuestion, submitted_answer: str) -> dict:
    correct_flag = is_correct(submitted_answer, question.correct_answer)

    attempt = Attempt(
        student_id=student_id,
        subject=question.subject,
        topic=question.topic,
        question=question.prompt,
        submitted_answer=submitted_answer,
        correct_answer=question.correct_answer,
        is_correct=1 if correct_flag else 0,
        difficulty=question.difficulty,
    )
    db.add(attempt)

    progress = db.scalar(
        select(Progress).where(
            Progress.student_id == student_id,
            Progress.subject == question.subject,
            Progress.topic == question.topic,
        )
    )
    if not progress:
        progress = Progress(student_id=student_id, subject=question.subject, topic=question.topic)
        db.add(progress)

    progress.attempted += 1
    progress.correct += 1 if correct_flag else 0
    raw_accuracy = progress.correct / progress.attempted
    progress.mastery = round(raw_accuracy * 100, 1)

    if progress.attempted >= 5:
        if progress.mastery >= 85 and progress.difficulty < 5:
            progress.difficulty += 1
        elif progress.mastery < 55 and progress.difficulty > 1:
            progress.difficulty -= 1

    question.answered_at = datetime.utcnow()
    progress.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(progress)

    return {
        "is_correct": correct_flag,
        "correct_answer": question.correct_answer if not correct_flag else None,
        "mastery": progress.mastery,
        "next_difficulty": progress.difficulty,
        "feedback": "Great job! 🌟" if correct_flag else f"Good try. The correct answer is {question.correct_answer}. We'll practice this again. 💪",
    }
