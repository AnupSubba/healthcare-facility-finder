"""Emergency detection in plain code. Runs before any AI call, so it works even if every LLM is down.

Words that describe a *service* ("hospital with emergency", "24x7") are not triggers; words that
describe a *situation* are. The list deliberately errs on the side of caution: showing the emergency
numbers unnecessarily is far better than missing a real emergency.
"""

import re

PHRASES = [
    # English
    "chest pain",
    "heart attack",
    "cardiac arrest",
    "stroke",
    "not breathing",
    "cant breathe",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "breathing problem",
    "unconscious",
    "fainted",
    "collapsed",
    "accident",
    "severe bleeding",
    "bleeding heavily",
    "heavy bleeding",
    "seizure",
    "fits",
    "convulsion",
    "poison",
    "overdose",
    "suicide",
    "kill myself",
    "snake bite",
    "snakebite",
    "dog bite",
    "burn",
    "drowning",
    "choking",
    "electric shock",
    "head injury",
    "fracture",
    "labour pain",
    "labor pain",
    "pregnancy emergency",
    "ambulance",
    "dying",
    "very serious",
    # Hindi / Hinglish (Latin script)
    "seene mein dard",
    "seene me dard",
    "dil ka daura",
    "saans nahi",
    "saans nahin",
    "saans lene mein",
    "behosh",
    "khoon beh",
    "khoon nikal",
    "durghatna",
    "accident ho gaya",
    "jahar",
    "zeher",
    "zehar",
    "saanp ne kaata",
    "dauraa",
    "mirgi",
    "jal gaya",
    "jal gayi",
    "jaldi doctor",
    # Hindi (Devanagari)
    "सीने में दर्द",
    "दिल का दौरा",
    "सांस नहीं",
    "साँस नहीं",
    "बेहोश",
    "खून बह",
    "दुर्घटना",
    "एक्सीडेंट",
    "ज़हर",
    "जहर",
    "सांप ने काटा",
    "मिर्गी",
    "जल गया",
    "जल गई",
    "एम्बुलेंस",
]

_PATTERNS = [re.compile(r"(?<!\w)" + re.escape(p) + r"(?!\w)") for p in PHRASES]


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    return re.sub(r"\s+", " ", text).strip()


def is_emergency(text: str) -> bool:
    t = normalize(text)
    return any(p.search(t) for p in _PATTERNS)
