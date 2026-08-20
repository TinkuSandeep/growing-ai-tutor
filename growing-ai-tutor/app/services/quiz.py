import random


TOPICS = {
    "Maths": ["Addition", "Subtraction", "Multiplication"],
    "Logical Reasoning": ["Patterns", "Sequences", "Odd One Out"],
}


def _cap(difficulty: int) -> int:
    return {1: 10, 2: 20, 3: 50, 4: 100, 5: 500}.get(difficulty, 20)


def generate_question(subject: str, topic: str, difficulty: int = 1) -> dict:
    difficulty = max(1, min(5, difficulty))
    cap = _cap(difficulty)

    if subject == "Maths" and topic == "Addition":
        a, b = random.randint(0, cap), random.randint(0, cap)
        return _q(subject, topic, f"What is {a} + {b}?", str(a + b), difficulty)

    if subject == "Maths" and topic == "Subtraction":
        a = random.randint(1, cap)
        b = random.randint(0, a)
        return _q(subject, topic, f"What is {a} - {b}?", str(a - b), difficulty)

    if subject == "Maths" and topic == "Multiplication":
        upper = min(12, 3 + difficulty * 2)
        a, b = random.randint(1, upper), random.randint(1, upper)
        return _q(subject, topic, f"What is {a} × {b}?", str(a * b), difficulty)

    if subject == "Logical Reasoning" and topic == "Patterns":
        start = random.randint(1, 10)
        step = random.randint(1, 2 + difficulty)
        seq = [start + i * step for i in range(4)]
        return _q(subject, topic, f"What comes next? {', '.join(map(str, seq))}, ?", str(seq[-1] + step), difficulty)

    if subject == "Logical Reasoning" and topic == "Sequences":
        start = random.randint(2, 6)
        seq = [start]
        for _ in range(3):
            seq.append(seq[-1] * 2)
        return _q(subject, topic, f"Find the next number: {', '.join(map(str, seq))}, ?", str(seq[-1] * 2), difficulty)

    if subject == "Logical Reasoning" and topic == "Odd One Out":
        groups = [
            (["2", "4", "6", "7"], "7"),
            (["cat", "dog", "cow", "car"], "car"),
            (["circle", "square", "triangle", "mango"], "mango"),
        ]
        values, answer = random.choice(groups)
        return _q(subject, topic, f"Which is the odd one out? {', '.join(values)}", answer, difficulty)

    raise ValueError(f"Unsupported subject/topic: {subject}/{topic}")


def _q(subject: str, topic: str, question: str, answer: str, difficulty: int) -> dict:
    return {
        "subject": subject,
        "topic": topic,
        "question": question,
        "correct_answer": answer,
        "difficulty": difficulty,
    }


def is_correct(submitted: str, correct: str) -> bool:
    return submitted.strip().casefold() == correct.strip().casefold()
