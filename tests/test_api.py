import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_MOCK", "1")
    monkeypatch.chdir(tmp_path)            # keep outputs/runs.jsonl out of the repo during tests
    from backend.app import app
    return TestClient(app)

def test_health_reports_mock(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["mock"] is True

def test_versions_include_final(client):
    v = client.get("/api/versions").json()
    assert "final" in v["versions"] and "v1" in v["versions"]

def test_decompose_ok(client):
    r = client.post("/api/decompose", json={"question": "What are the main challenges of deploying LLMs in production?"})
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ok" and body["mock"] is True
    assert 3 <= len(body["decomposition"]["sub_questions"]) <= 6

def test_short_input_not_researchable(client):
    body = client.post("/api/decompose", json={"question": "hello"}).json()
    assert body["status"] == "not_researchable" and body["decomposition"] is None

def test_unknown_version_400(client):
    r = client.post("/api/decompose", json={"question": "What are the main challenges here?", "version": "nope"})
    assert r.status_code == 400

def test_empty_question_422(client):
    assert client.post("/api/decompose", json={"question": ""}).status_code == 422

def test_frontend_is_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Research Assistant" in r.text
    assert client.get("/app.js").status_code == 200 and client.get("/style.css").status_code == 200
