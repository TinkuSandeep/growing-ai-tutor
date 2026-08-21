from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    grade: int = Field(default=2, ge=1, le=12)
    preferred_language: str = Field(default="both", pattern="^(english|telugu|both)$")


class StudentOut(BaseModel):
    id: int
    display_name: str
    grade: int
    preferred_language: str
    beta_code: str

    model_config = {"from_attributes": True}


class StudentLanguageUpdate(BaseModel):
    preferred_language: str = Field(pattern="^(english|telugu|both)$")


class QuizAnswer(BaseModel):
    student_id: int
    question_id: int
    submitted_answer: str = Field(max_length=120)


class TutorRequest(BaseModel):
    student_id: int
    subject: str
    topic: str
    question: str | None = None
    language: str | None = Field(default=None, pattern="^(english|telugu|both)$")


class AbacusRequest(BaseModel):
    number: int = Field(ge=0, le=9999)


class FeedbackCreate(BaseModel):
    student_id: int | None = None
    useful_rating: str = Field(pattern="^(yes|little|no)$")
    difficulty_rating: str = Field(pattern="^(easy|right|hard)$")
    preferred_language: str = Field(pattern="^(english|telugu|both)$")
    regular_use: str = Field(pattern="^(yes|maybe|no)$")
    willingness_to_pay: str = Field(pattern="^(99|149|199|free)$")
    requested_features: str = Field(default="", max_length=1000)
    comments: str = Field(default="", max_length=2000)
