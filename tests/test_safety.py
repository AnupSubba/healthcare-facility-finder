import pytest

from facility_finder.agent.safety import is_emergency


@pytest.mark.parametrize(
    "text",
    [
        "chest pain",
        "My father has CHEST PAIN, which hospital?",
        "accident ho gaya, hospital kahan hai",
        "someone is unconscious",
        "she can't breathe",
        "Saans nahi aa rahi",
        "behosh ho gaye",
        "सीने में दर्द है",
        "बेहोश हो गए",
        "snake bite in village near Patna",
        "need an ambulance",
    ],
)
def test_emergencies_are_caught(text):
    assert is_emergency(text)


@pytest.mark.parametrize(
    "text",
    [
        "government hospital with emergency in Lucknow",
        "NABL lab near 110017",
        "What is NABH?",
        "private clinic in Indiranagar Bangalore",
        "Lucknow mein sarkari aspatal",
        "burnside clinic",  # "burn" must match a whole word only
    ],
)
def test_normal_questions_are_not_emergencies(text):
    assert not is_emergency(text)
