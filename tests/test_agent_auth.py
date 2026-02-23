from fastapi.testclient import TestClient

from interface import routes as routes_module
from main import app

client = TestClient(app)


def test_agent_register_rejects_invalid_secret():
    response = client.post("/api/agent/register", json={"agent_secret": "bad-secret"})
    assert response.status_code == 400
    assert "challenge" in response.json()["detail"].lower()


def test_agent_register_success_and_bearer_auth(monkeypatch):
    def fake_validate(secret: str) -> tuple[bool, str]:
        return True, "ABCDEFGHZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZMTL"

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)

    reg = client.post(
        "/api/agent/register",
        json={"agent_secret": "any-secret", "agent_name": "bot"},
    )
    assert reg.status_code == 200
    body = reg.json()
    assert "agent_id" in body
    assert "bearer_token" in body
    assert "created" in body
    token = body["bearer_token"]

    missing = client.get("/api/agent/me")
    assert missing.status_code == 401

    invalid = client.get("/api/agent/me", headers={"Authorization": "Bearer bad"})
    assert invalid.status_code == 403

    ok = client.get("/api/agent/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["agent_id"] == body["agent_id"]
