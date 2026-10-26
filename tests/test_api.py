from fastapi.testclient import TestClient

from facility_finder import config
from facility_finder.api import main


def client(monkeypatch, api_key=""):
    monkeypatch.setattr(config, "API_KEY", api_key)
    main.limiter.reset()
    return TestClient(main.app)


def fake_ask(question, lat=None, lon=None):
    return {"answer": "ok", "results": [], "needs_location": False, "emergency": False, "sources": []}


def test_health(monkeypatch):
    assert client(monkeypatch).get("/health").json()["status"] == "ok"


def test_ask_requires_api_key_when_set(monkeypatch):
    monkeypatch.setattr(main.graph, "ask", fake_ask)
    c = client(monkeypatch, api_key="secret")
    assert c.post("/ask", json={"question": "hospital in Pune"}).status_code == 401
    ok = c.post("/ask", json={"question": "hospital in Pune"}, headers={"x-api-key": "secret"})
    assert ok.status_code == 200 and ok.json()["answer"] == "ok"


def test_question_length_is_limited(monkeypatch):
    c = client(monkeypatch)
    assert c.post("/ask", json={"question": "x" * 301}).status_code == 422


def test_location_outside_india_is_rejected(monkeypatch):
    c = client(monkeypatch)
    assert c.post("/ask", json={"question": "hospital", "lat": 51.5, "lon": -0.1}).status_code == 422


def test_rate_limit(monkeypatch):
    monkeypatch.setattr(main.graph, "ask", fake_ask)
    c = client(monkeypatch)
    codes = [c.post("/ask", json={"question": "hospital in Pune"}).status_code for _ in range(22)]
    assert codes[:20] == [200] * 20 and codes[-1] == 429


def test_errors_become_503(monkeypatch):
    def broken(*a, **k):
        raise RuntimeError("database down")

    monkeypatch.setattr(main.graph, "ask", broken)
    assert client(monkeypatch).post("/ask", json={"question": "hospital in Pune"}).status_code == 503
