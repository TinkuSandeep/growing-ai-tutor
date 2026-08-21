from app.services.quiz import generate_question


def test_science_question_supported():
    q = generate_question("Science", "Plants", 1)
    assert q["subject"] == "Science"
    assert q["topic"] == "Plants"
    assert q["correct_answer"]
