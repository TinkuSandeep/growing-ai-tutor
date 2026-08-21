from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import QuizQuestion, Student
from app.services.progress import record_attempt


def test_first_attempt_creates_progress_and_returns_feedback():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        student = Student(display_name="Beta Kid", grade=2)
        question = QuizQuestion(
            subject="Maths",
            topic="Addition",
            prompt="What is 6 + 8?",
            correct_answer="14",
            difficulty=1,
        )
        db.add_all([student, question])
        db.commit()
        db.refresh(student)
        db.refresh(question)

        result = record_attempt(
            db,
            student_id=student.id,
            question=question,
            submitted_answer="14",
        )

        assert result["is_correct"] is True
        assert result["mastery"] == 100.0
        assert "Great job" in result["feedback"]
