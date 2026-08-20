from app.config import get_settings

settings = get_settings()


def explain_for_child(*, grade: int, subject: str, topic: str, question: str | None = None) -> dict:
    if not settings.openai_api_key:
        return {"mode": "offline", "text": offline_explanation(grade, subject, topic)}

    # Lazy import keeps the deterministic/offline tutor runnable without the optional SDK.
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
You are a warm, patient tutor for a Grade {grade} child.
Subject: {subject}
Topic: {topic}
Question/context: {question or 'Teach the core idea.'}

Rules:
- Use age-appropriate language and short explanations.
- Ask at most one small check-for-understanding question at the end.
- Encourage reasoning, not memorization alone.
- Never ask for personal details.
- Do not browse the web or suggest contacting strangers.
- For arithmetic, explain the concept but do not invent a different answer than deterministic app logic.
""".strip()

    response = client.responses.create(model=settings.openai_model, input=prompt)
    return {"mode": "ai", "text": response.output_text}


def offline_explanation(grade: int, subject: str, topic: str) -> str:
    guides = {
        ("Maths", "Addition"): "Addition means putting groups together. Try counting on from the bigger number.",
        ("Maths", "Subtraction"): "Subtraction means finding what is left after some are taken away.",
        ("Maths", "Multiplication"): "Multiplication is a quick way to add equal groups.",
        ("Logical Reasoning", "Patterns"): "A pattern follows a rule. Look at how each item changes from the one before it.",
        ("Logical Reasoning", "Sequences"): "A sequence is an ordered list. Find the rule connecting the numbers.",
        ("Logical Reasoning", "Odd One Out"): "Look for three things that belong together, then find the one that does not match.",
    }
    text = guides.get((subject, topic), f"Let's learn {topic} step by step.")
    return f"Grade {grade}: {text}"
