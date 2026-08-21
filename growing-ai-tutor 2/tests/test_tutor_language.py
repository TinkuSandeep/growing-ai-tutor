from app.services.tutor import offline_explanation


def test_bilingual_offline_tutor_contains_telugu_and_english():
    text = offline_explanation(2, "Maths", "Addition", "both")
    assert "Addition" in text
    assert "అంటే" in text
