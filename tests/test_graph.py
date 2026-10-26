"""Agent routing tests with fake extraction, search and explain functions (no LLM, no database)."""

from facility_finder.agent.graph import build_graph
from facility_finder.models import FacilitySearch

ROW = {"id": 1, "name": "District Hospital", "type": "hospital", "emergency": True}


def make(extracted: FacilitySearch | Exception, rows=(ROW,), emergency_rows=True):
    calls = []

    def extract(question):
        if isinstance(extracted, Exception):
            raise extracted
        return extracted

    def search(f, lat=None, lon=None):
        calls.append(f)
        if f.emergency_only and not emergency_rows:
            return []
        return list(rows)

    def explain(question, language):
        return ("NABH accredits hospitals.", ["https://nabh.co"])

    return build_graph(extract_fn=extract, search_fn=search, explain_fn=explain), calls


def run(graph, question, **kw):
    return graph.invoke({"question": question, **kw})


def test_find_with_city_searches():
    g, calls = make(FacilitySearch(intent="find", facility_type="hospital", city="Lucknow"))
    out = run(g, "hospital in Lucknow")
    assert out["results"] == [ROW]
    assert calls[0].city == "Lucknow"
    assert "112" not in out["answer"]


def test_no_location_asks_for_one():
    g, calls = make(FacilitySearch(intent="find", facility_type="hospital", near_me=True))
    out = run(g, "hospital near me")
    assert out["needs_location"] is True and calls == []


def test_location_from_browser_is_enough():
    g, calls = make(FacilitySearch(intent="find", near_me=True))
    out = run(g, "clinic near me", lat=28.6, lon=77.2)
    assert out["results"] and calls


def test_pincode_typed_by_user_is_never_lost():
    g, calls = make(FacilitySearch(intent="find", facility_type="lab"))  # LLM forgot the pincode
    run(g, "lab near 110017")
    assert calls[0].pincode == "110017"


def test_emergency_shows_numbers_and_forces_hospital():
    g, calls = make(FacilitySearch(intent="find", city="Jaipur"))
    out = run(g, "chest pain, hospital in Jaipur")
    assert out["answer"].startswith("🚨") and "112" in out["answer"]
    assert calls[0].facility_type == "hospital" and calls[0].emergency_only


def test_emergency_still_works_when_llm_fails():
    g, _ = make(RuntimeError("LLM down"))
    out = run(g, "accident ho gaya")
    assert "112" in out["answer"] and out["needs_location"] is True


def test_emergency_falls_back_to_any_hospital():
    g, calls = make(FacilitySearch(intent="find", city="Patna"), emergency_rows=False)

    out = run(g, "unconscious person, hospital in Patna")
    assert out["results"], "should fall back to hospitals without the emergency tag"
    assert calls[0].emergency_only and not calls[-1].emergency_only


def test_llm_failure_without_emergency_gives_friendly_error():
    g, _ = make(RuntimeError("LLM down"))
    out = run(g, "hospital in Pune")
    assert "Sorry" in out["answer"]


def test_medical_question_is_declined():
    g, calls = make(FacilitySearch(intent="out_of_scope"))
    out = run(g, "what medicine for fever?")
    assert "can't give medical advice" in out["answer"] and calls == []


def test_explain_uses_glossary():
    g, _ = make(FacilitySearch(intent="explain"))
    out = run(g, "What is NABH?")
    assert out["sources"] == ["https://nabh.co"]


def test_hindi_script_gets_hindi_answer():
    g, _ = make(FacilitySearch(intent="find", facility_type="hospital", language="en"))
    out = run(g, "पटना में सरकारी अस्पताल")  # no city extracted -> asks for location, in Hindi
    assert "शहर" in out["answer"]
