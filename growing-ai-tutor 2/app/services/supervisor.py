from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Progress


def recommend_next(db: Session, student_id: int) -> dict:
    rows = list(db.scalars(select(Progress).where(Progress.student_id == student_id)).all())
    if not rows:
        return {
            "action": "learn",
            "subject": "Maths",
            "topic": "Addition",
            "reason": "Start with a friendly foundation lesson.",
        }

    weakest = min(rows, key=lambda p: (p.mastery, p.attempted))
    if weakest.mastery < 60:
        action = "learn"
        reason = "This topic needs another explanation before more practice."
    elif weakest.mastery < 85:
        action = "practice"
        reason = "A few more questions should strengthen this topic."
    else:
        action = "challenge"
        reason = "Performance is strong, so increase the challenge gradually."

    return {
        "action": action,
        "subject": weakest.subject,
        "topic": weakest.topic,
        "difficulty": weakest.difficulty,
        "mastery": weakest.mastery,
        "reason": reason,
    }
