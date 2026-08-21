from app.models import Feedback


def test_feedback_model_exists():
    assert Feedback.__tablename__ == "feedback"
