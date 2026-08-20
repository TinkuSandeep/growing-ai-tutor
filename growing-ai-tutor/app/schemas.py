from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    grade: int = Field(default=2, ge=1, le=12)


class StudentOut(BaseModel):
    id: int
    display_name: str
    grade: int

    model_config = {"from_attributes": True}


class QuizAnswer(BaseModel):
    student_id: int
    question_id: int
    submitted_answer: str = Field(max_length=120)


class TutorRequest(BaseModel):
    student_id: int
    subject: str
    topic: str
    question: str | None = None


class AbacusRequest(BaseModel):
    number: int = Field(ge=0, le=9999)
