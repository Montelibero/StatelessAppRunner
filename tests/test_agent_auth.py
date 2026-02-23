from fastapi.testclient import TestClient

from interface import routes as routes_module
from main import app

client = TestClient(app)


def test_agent_register_challenge_endpoint():
    response = client.post("/api/agent/register/challenge", json={})
    assert response.status_code == 200
    body = response.json()
    assert "pow_challenge" in body
    assert "pow_bits" in body
    assert "expires_at" in body


def test_validate_agent_secret_accepts_non_empty_and_derives_mtla_id():
    ok, agent_id = routes_module.validate_agent_secret("seed")
    assert ok is True
    assert agent_id.startswith("MTLA")

    empty_ok, _ = routes_module.validate_agent_secret(" ")
    assert empty_ok is False


def test_agent_register_rejects_invalid_secret():
    response = client.post(
        "/api/agent/register",
        json={"agent_secret": "bad-secret", "pow_challenge": "x.y", "pow_nonce": "1"},
    )
    assert response.status_code == 400
    assert (
        "pow" in response.json()["detail"].lower()
        or "challenge" in response.json()["detail"].lower()
    )


def test_agent_register_requires_pow_nonce():
    response = client.post("/api/agent/register", json={"agent_secret": "seed"})
    assert response.status_code == 400
    assert "pow" in response.json()["detail"].lower()


def test_agent_register_success_and_bearer_auth(monkeypatch):
    def fake_validate(secret: str) -> tuple[bool, str]:
        return True, "ABCDEFGHZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZMTL"

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)
    monkeypatch.setattr(
        routes_module,
        "verify_registration_pow",
        lambda *_args, **_kwargs: True,
    )

    reg = client.post(
        "/api/agent/register",
        json={
            "agent_secret": "any-secret",
            "pow_challenge": "x.y",
            "pow_nonce": "1",
            "agent_name": "bot",
        },
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
