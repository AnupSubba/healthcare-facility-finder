"""Healthcare Facility Finder: Streamlit UI. Talks only to the API; it never sees LLM or database keys.

Local:  uv run streamlit run ui/app.py     (with the API running on http://localhost:8000)
"""

import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Healthcare Facility Finder", page_icon="🏥", layout="wide")


def setting(name: str, default: str = "") -> str:
    try:
        return st.secrets[name]
    except Exception:  # no secrets file locally
        return os.getenv(name, default)


API_URL = setting("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = setting("API_KEY")

TEXT = {
    "English": {
        "banner": "🚨 In an emergency, call **112** (all emergencies) or **108** (ambulance).",
        "title": "Find hospitals, clinics and labs",
        "caption": "Information only, not medical advice. Please don't type personal health details.",
        "pincode": "Pincode (optional)",
        "ask": "e.g. Government hospital with emergency in Lucknow",
        "waking": "Searching… the first search can take up to a minute while the server wakes up.",
        "call": "Call",
        "directions": "Directions",
        "source": "Source",
        "updated": "updated",
        "report": "Report incorrect info",
        "report_hint": "What's wrong? (no personal details)",
        "send": "Send",
        "thanks": "Thank you! We'll check it.",
        "busy": "Too many searches right now. Please wait a minute and try again.",
        "down": "The search service isn't responding. Please try again in a minute.",
        "away": "km away",
    },
    "हिन्दी": {
        "banner": "🚨 आपात स्थिति में **112** (सभी आपात स्थितियाँ) या **108** (एम्बुलेंस) पर कॉल करें।",
        "title": "अस्पताल, क्लिनिक और लैब खोजें",
        "caption": "केवल जानकारी के लिए, चिकित्सा सलाह नहीं। कृपया अपनी निजी स्वास्थ्य जानकारी न लिखें।",
        "pincode": "पिनकोड (वैकल्पिक)",
        "ask": "जैसे: लखनऊ में इमरजेंसी वाला सरकारी अस्पताल",
        "waking": "खोज जारी है… पहली खोज में एक मिनट तक लग सकता है।",
        "call": "कॉल करें",
        "directions": "रास्ता देखें",
        "source": "स्रोत",
        "updated": "अपडेट",
        "report": "गलत जानकारी बताएँ",
        "report_hint": "क्या गलत है? (निजी जानकारी न लिखें)",
        "send": "भेजें",
        "thanks": "धन्यवाद! हम जाँच करेंगे।",
        "busy": "अभी बहुत सारी खोजें हो रही हैं। एक मिनट बाद फिर कोशिश करें।",
        "down": "खोज सेवा अभी जवाब नहीं दे रही। एक मिनट बाद फिर कोशिश करें।",
        "away": "किमी दूर",
    },
}


def call_api(path: str, payload: dict) -> requests.Response:
    return requests.post(f"{API_URL}{path}", json=payload, headers={"x-api-key": API_KEY}, timeout=90)


def show_facility(f: dict, t: dict) -> None:
    with st.container(border=True):
        badge = " · ".join(x.title() for x in (f["type"], f["ownership"]) if x and x != "unknown")
        st.markdown(f"**{f['name']}**  \n{badge}")
        place = ", ".join(str(x) for x in (f.get("address"), f.get("city"), f.get("pincode")) if x)
        if place:
            st.write(place)
        if f.get("distance_m") is not None:
            st.caption(f"{f['distance_m'] / 1000:.1f} {t['away']}")
        links = []
        if f.get("phone"):
            links.append(f"[📞 {t['call']} {f['phone']}](tel:{f['phone']})")
        if f.get("lat") is not None:
            links.append(
                f"[🧭 {t['directions']}](https://www.google.com/maps/dir/?api=1&destination={f['lat']},{f['lon']})"
            )
        if links:
            st.markdown(" · ".join(links))
        sources = ", ".join(
            s["source"].replace("data_gov", "data.gov.in").replace("osm", "OpenStreetMap") for s in f["sources"]
        )
        st.caption(f"{t['source']}: {sources} · {t['updated']} {f['updated_on']}")
        with st.popover(t["report"]):
            issue = st.text_input(t["report_hint"], key=f"issue-{f['id']}", max_chars=500)
            if st.button(t["send"], key=f"send-{f['id']}") and len(issue.strip()) >= 3:
                try:
                    call_api("/reports", {"facility_id": f["id"], "issue": issue})
                    st.success(t["thanks"])
                except requests.RequestException:
                    st.error(t["down"])


language = st.sidebar.radio("Language / भाषा", list(TEXT), horizontal=True)
t = TEXT[language]

st.error(t["banner"])
st.title(t["title"])
st.caption(t["caption"])

pincode = st.text_input(t["pincode"], max_chars=6)
question = st.chat_input(t["ask"])

if question:
    q = f"{question} {pincode}".strip() if pincode.strip() else question
    with st.spinner(t["waking"]):
        try:
            response = call_api("/ask", {"question": q[:300]})
            if response.status_code == 429:
                st.session_state.result = {"error": t["busy"]}
            elif response.ok:
                st.session_state.result = response.json()
            else:
                st.session_state.result = {"error": t["down"]}
        except requests.RequestException:
            st.session_state.result = {"error": t["down"]}
    st.session_state.question = question

result = st.session_state.get("result")
if result:
    st.markdown(f"> {st.session_state.get('question', '')}")
    if "error" in result:
        st.warning(result["error"])
    else:
        st.write(result["answer"])
        for url in result.get("sources") or []:
            st.caption(f"Source: {url}")
        rows = result.get("results") or []
        located = pd.DataFrame([r for r in rows if r.get("lat") is not None])
        if not located.empty:
            st.map(located, latitude="lat", longitude="lon", size=40)
        for facility in rows:
            show_facility(facility, t)

st.divider()
st.caption(
    "Data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL) and data.gov.in "
    "(Government Open Data License - India). Listings may be incomplete or out of date: please call ahead."
)
