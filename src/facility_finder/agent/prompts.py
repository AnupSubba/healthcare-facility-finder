"""Prompt for filter extraction, and the fixed answer templates (English and Hindi)."""

EXTRACT_SYSTEM = """You turn a question about finding healthcare facilities in India into search filters.
You never answer the question yourself and never give medical advice.

Fields:
- intent: "find" (looking for a hospital, clinic or lab), "explain" (asking what a term means, e.g. NABH, NABL,
  PM-JAY, CGHS, or how this app works), "emergency" (someone needs urgent care), "out_of_scope" (medical advice,
  diagnosis, medicines, test results, or anything else).
- facility_type: "hospital", "clinic" or "lab" (diagnostic lab, pathology, blood test, x-ray, scan). Empty if not stated.
- city: city or town in English spelling (Bengaluru, Mumbai, Lucknow). Empty if not stated.
- pincode: 6-digit pincode if present.
- near_me: true if the user says near me, nearby, close by, paas, aas-paas, nazdeek.
- ownership: "government" for government, govt, sarkari, public; "private" for private. Empty if not stated.
- emergency_only: true if the user asks for emergency / casualty / 24x7 services.
- name_contains: part of a facility name only if the user names a specific facility.
- language: "hi" if the question is in Hindi or Hinglish, otherwise "en".

Leave a field empty rather than guessing. Never invent a city or pincode.

Examples:
"government hospital with emergency in Lucknow" -> intent=find, facility_type=hospital, city=Lucknow, ownership=government, emergency_only=true, language=en
"NABL lab near 110017" -> intent=find, facility_type=lab, pincode=110017, near_me=true, language=en
"private clinic in Indiranagar Bangalore" -> intent=find, facility_type=clinic, city=Bengaluru, ownership=private, language=en
"hospital near me" -> intent=find, facility_type=hospital, near_me=true, language=en
"Lucknow mein sarkari aspatal" -> intent=find, facility_type=hospital, city=Lucknow, ownership=government, language=hi
"Pune mein blood test ke liye lab kahan hai" -> intent=find, facility_type=lab, city=Pune, language=hi
"पटना में सरकारी अस्पताल" -> intent=find, facility_type=hospital, city=Patna, ownership=government, language=hi
"What is NABH?" -> intent=explain, language=en
"PM-JAY kya hai" -> intent=explain, language=hi
"What medicine should I take for fever?" -> intent=out_of_scope, language=en
"Is my sugar level of 180 normal?" -> intent=out_of_scope, language=en
"chest pain, which hospital in Jaipur" -> intent=emergency, facility_type=hospital, city=Jaipur, emergency_only=true, language=en
"""

TEMPLATES = {
    "en": {
        "emergency": "🚨 In an emergency, call 112 (all emergencies) or 108 (ambulance) now.",
        "found": "I found {n} matching places. Please call ahead to confirm services and timings.",
        "found_fallback": "I couldn't find exact matches, so here are {n} nearby hospitals.",
        "none": "I couldn't find matching places. Try a nearby city or pincode, or remove a filter such as government/private.",
        "where": "Which city or pincode should I search in? You can also share your location.",
        "decline": "I can't give medical advice, diagnoses or medicine suggestions. Please speak to a doctor. "
        "I can help you find a nearby hospital or clinic: tell me your city or pincode.",
        "error": 'Sorry, I couldn\'t understand that. Try something like "government hospital in Lucknow" or "lab near 110017".',
    },
    "hi": {
        "emergency": "🚨 आपात स्थिति में तुरंत 112 (सभी आपात स्थितियाँ) या 108 (एम्बुलेंस) पर कॉल करें।",
        "found": "मुझे {n} जगहें मिलीं। जाने से पहले फ़ोन करके सेवाएँ और समय की पुष्टि कर लें।",
        "found_fallback": "सटीक परिणाम नहीं मिले, इसलिए आस-पास के {n} अस्पताल दिखाए गए हैं।",
        "none": "कोई मिलती-जुलती जगह नहीं मिली। पास का शहर या पिनकोड आज़माएँ, या सरकारी/प्राइवेट जैसा फ़िल्टर हटाएँ।",
        "where": "किस शहर या पिनकोड में खोजूँ? आप अपनी लोकेशन भी साझा कर सकते हैं।",
        "decline": "मैं चिकित्सा सलाह, निदान या दवा नहीं बता सकता। कृपया डॉक्टर से बात करें। "
        "मैं पास का अस्पताल या क्लिनिक खोजने में मदद कर सकता हूँ: अपना शहर या पिनकोड बताएँ।",
        "error": 'माफ़ कीजिए, मैं समझ नहीं पाया। ऐसे लिखें: "लखनऊ में सरकारी अस्पताल" या "110017 के पास लैब"।',
    },
}
