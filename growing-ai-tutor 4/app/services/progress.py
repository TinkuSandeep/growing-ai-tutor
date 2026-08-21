from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Progress, QuizQuestion
from app.services.quiz import is_correct


def record_attempt(
    db: Session,
    *,
    student_id: int,
    question: QuizQuestion,
    submitted_answer: str,
) -> dict:
    """Record a quiz attempt, update mastery, and return child-friendly feedback."""

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
        progress = Progress(
            student_id=student_id,
            subject=question.subject,
            topic=question.topic,
            attempted=0,
            correct=0,
            mastery=0.0,
            difficulty=1,
        )
        db.add(progress)

    progress.attempted = (progress.attempted or 0) + 1
    progress.correct = (progress.correct or 0) + (1 if correct_flag else 0)

    raw_accuracy = progress.correct / progress.attempted if progress.attempted else 0
    progress.mastery = round(raw_accuracy * 100, 1)

    current_difficulty = progress.difficulty or 1
    if progress.attempted >= 5:
        if progress.mastery >= 85 and current_difficulty < 5:
            current_difficulty += 1
        elif progress.mastery < 55 and current_difficulty > 1:
            current_difficulty -= 1
    progress.difficulty = current_difficulty

    question.answered_at = datetime.utcnow()
    progress.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)

    if correct_flag:
        feedback = "Great job! 🌟 That's correct."
        if progress.mastery >= 85:
            feedback += " You're doing really well on this topic! 🚀"
        elif progress.mastery >= 60:
            feedback += " Keep practicing — you're getting stronger! 💪"
    else:
        feedback = (
            f"Good try! 🙂 The correct answer is {question.correct_answer}. "
            "Let's practice another one."
        )

    return {
        "is_correct": correct_flag,
        "correct_answer": None if correct_flag else question.correct_answer,
        "mastery": progress.mastery,
        "next_difficulty": progress.difficulty,
        "feedback": feedback,
    }
