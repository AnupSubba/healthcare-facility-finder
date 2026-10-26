"""UI smoke tests with Streamlit AppTest; the API is replaced by a fake."""

import pytest
import requests
from streamlit.testing.v1 import AppTest

RESULT = {
    "answer": "I found 1 matching places.",
    "results": [
        {
            "id": 7,
            "name": "District Hospital",
            "type": "hospital",
            "ownership": "government",
            "address": "MG Road",
            "city": "Lucknow",
            "pincode": "226001",
            "phone": "5221234567",
            "emergency": True,
            "lat": 26.85,
            "lon": 80.95,
            "distance_m": None,
            "sources": [{"source": "osm", "id": "node/1", "url": "https://www.openstreetmap.org/node/1"}],
            "updated_on": "2026-10-26",
        }
    ],
    "needs_location": False,
    "emergency": False,
    "sources": [],
}


class FakeResponse:
    def __init__(self, status, body):
        self.status_code, self._body = status, body
        self.ok = 200 <= status < 300

    def json(self):
        return self._body


@pytest.fixture
def app(monkeypatch):
    def run(status=200, body=RESULT):
        monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(status, body))
        return AppTest.from_file("../ui/app.py", default_timeout=30).run()

    return run


def test_emergency_banner_always_visible(app):
    at = app()
    assert not at.exception
    assert "112" in at.error[0].value and "108" in at.error[0].value


def test_results_are_shown(app):
    at = app()
    at.chat_input[0].set_value("government hospital in Lucknow").run()
    text = " ".join(m.value for m in at.markdown)
    assert "District Hospital" in text and "tel:5221234567" in text


def test_rate_limit_message(app):
    at = app(status=429, body={})
    at.chat_input[0].set_value("hospital in Pune").run()
    assert at.warning and "Too many" in at.warning[0].value


def test_hindi_labels(app):
    at = app()
    at.sidebar.radio[0].set_value("हिन्दी").run()
    assert "अस्पताल" in at.title[0].value
