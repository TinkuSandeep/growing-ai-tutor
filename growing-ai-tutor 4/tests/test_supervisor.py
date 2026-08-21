from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Progress, Student
from app.services.supervisor import recommend_next


def test_supervisor_starts_with_addition():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        student = Student(display_name="Test", grade=2)
        db.add(student)
        db.commit(); db.refresh(student)
        rec = recommend_next(db, student.id)
        assert rec["topic"] == "Addition"


def test_supervisor_targets_weakest_topic():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        student = Student(display_name="Test", grade=2)
        db.add(student); db.commit(); db.refresh(student)
        db.add_all([
            Progress(student_id=student.id, subject="Maths", topic="Addition", mastery=90, attempted=10),
            Progress(student_id=student.id, subject="Maths", topic="Subtraction", mastery=45, attempted=8),
        ])
        db.commit()
        rec = recommend_next(db, student.id)
        assert rec["topic"] == "Subtraction"
        assert rec["action"] == "learn"
