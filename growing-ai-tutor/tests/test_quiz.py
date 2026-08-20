from app.services.quiz import generate_question, is_correct


def test_addition_question_is_self_consistent():
    q = generate_question("Maths", "Addition", 2)
    left = q["question"].replace("What is ", "").replace("?", "")
    a, b = [int(x.strip()) for x in left.split("+")]
    assert int(q["correct_answer"]) == a + b


def test_answer_normalization():
    assert is_correct(" Car ", "car")
