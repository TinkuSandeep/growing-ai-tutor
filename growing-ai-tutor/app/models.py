from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    progress: Mapped[list["Progress"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(40), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(40), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    submitted_answer: Mapped[str] = mapped_column(String(120))
    correct_answer: Mapped[str] = mapped_column(String(120))
    is_correct: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    student: Mapped[Student] = relationship(back_populates="attempts")


class Progress(Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("student_id", "subject", "topic", name="uq_progress_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(40), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    attempted: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    mastery: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped[Student] = relationship(back_populates="progress")
