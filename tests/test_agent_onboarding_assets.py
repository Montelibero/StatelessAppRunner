from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_skill_md_is_available():
    response = client.get("/skill.md")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "/api/agent/generate" in response.text


def test_llm_txt_is_available():
    response = client.get("/llm.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "POST /api/agent/generate" in response.text


def test_registration_scripts_are_available():
    py = client.get("/scripts/register_agent.py")
    js = client.get("/scripts/register_agent.mjs")

    assert py.status_code == 200
    assert js.status_code == 200
    assert "python" in py.text.lower()
    assert "node" in js.text.lower() or "mjs" in js.text.lower()
