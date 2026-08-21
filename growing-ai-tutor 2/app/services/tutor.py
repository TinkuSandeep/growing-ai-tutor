from app.config import get_settings

settings = get_settings()

LANGUAGE_NAMES = {
    "english": "English",
    "telugu": "Telugu",
    "both": "natural Telugu + English mixed language",
}


def explain_for_child(*, grade: int, subject: str, topic: str, question: str | None = None, language: str = "both") -> dict:
    language = language if language in LANGUAGE_NAMES else "both"
    if not settings.openai_api_key:
        return {"mode": "offline", "language": language, "text": offline_explanation(grade, subject, topic, language)}

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = f"""
You are a warm, patient personal tutor for an Indian Grade {grade} child.
Subject: {subject}
Topic: {topic}
Question/context: {question or 'Teach the core idea.'}
Teaching language: {LANGUAGE_NAMES[language]}.

Rules:
- Use age-appropriate language and short explanations.
- If language is Telugu, explain in clear conversational Telugu while retaining familiar English school terms when helpful.
- If language is mixed, speak naturally the way a Telugu-speaking parent/teacher might explain at home; do not mechanically translate every sentence.
- Use one concrete Indian/home/school example when useful.
- Ask at most one small check-for-understanding question at the end.
- Encourage reasoning, not memorization alone.
- Never ask for personal details.
- Do not browse the web or suggest contacting strangers.
- For arithmetic, explain the concept but do not invent a different answer than deterministic app logic.
""".strip()

    response = client.responses.create(model=settings.openai_model, input=prompt)
    return {"mode": "ai", "language": language, "text": response.output_text}


def offline_explanation(grade: int, subject: str, topic: str, language: str) -> str:
    english = {
        ("Maths", "Addition"): "Addition means putting groups together. Try counting on from the bigger number.",
        ("Maths", "Subtraction"): "Subtraction means finding what is left after some are taken away.",
        ("Maths", "Multiplication"): "Multiplication is a quick way to add equal groups.",
        ("Science", "Plants"): "Plants need water, air and light. Roots take in water, the stem supports the plant, and leaves help make food.",
        ("Science", "Animals"): "Animals can be grouped by what they eat, how they move and the body covering they have.",
        ("Science", "Our Body"): "Our body has organs that do different jobs. The heart pumps blood and the lungs help us breathe.",
        ("Logical Reasoning", "Patterns"): "A pattern follows a rule. Look at how each item changes from the one before it.",
        ("Logical Reasoning", "Sequences"): "A sequence is an ordered list. Find the rule connecting the numbers.",
        ("Logical Reasoning", "Odd One Out"): "Look for three things that belong together, then find the one that does not match.",
    }
    telugu = {
        ("Maths", "Addition"): "Addition అంటే రెండు లేదా ఎక్కువ groups ని కలపడం. పెద్ద number నుంచి ముందుకు count చేస్తూ చూడి.",
        ("Maths", "Subtraction"): "Subtraction అంటే కొంత తీసేసిన తర్వాత ఎంత మిగిలిందో కనుక్కోవడం.",
        ("Maths", "Multiplication"): "Multiplication అంటే equal groups ని త్వరగా add చేసే విధానం.",
        ("Science", "Plants"): "మొక్కలకు నీరు, గాలి, వెలుతురు అవసరం. Roots నీటిని తీసుకుంటాయి, stem మొక్కను నిలబెడుతుంది, leaves ఆహారం తయారుచేయడంలో సహాయపడతాయి.",
        ("Science", "Animals"): "Animals ను అవి ఏమి తింటాయి, ఎలా కదులుతాయి, వాటి body covering ఏంటి అనే దాని మీద groups గా చూడవచ్చు.",
        ("Science", "Our Body"): "మన body లో ప్రతి organ కి ఒక పని ఉంటుంది. Heart blood ని pump చేస్తుంది, lungs మనకు శ్వాస తీసుకోవడానికి సహాయపడతాయి.",
        ("Logical Reasoning", "Patterns"): "Pattern అంటే ఒక rule ప్రకారం మళ్లీ మళ్లీ వచ్చే మార్పు. ప్రతి item ముందు item నుంచి ఎలా మారిందో చూడు.",
        ("Logical Reasoning", "Sequences"): "Sequence అంటే order లో ఉన్న list. Numbers మధ్య ఉన్న rule ని కనుక్కో.",
        ("Logical Reasoning", "Odd One Out"): "మూడు items ఒకే group కి చెందుతున్నాయా చూడు; సరిపోని item odd one out.",
    }
    e = english.get((subject, topic), f"Let's learn {topic} step by step.")
    t = telugu.get((subject, topic), f"{topic} ని step by step నేర్చుకుందాం.")
    if language == "english":
        return f"Grade {grade}: {e}"
    if language == "telugu":
        return f"Grade {grade}: {t}"
    return f"Grade {grade}: {t}\n\nIn simple English: {e}"
