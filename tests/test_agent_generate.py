from fastapi.testclient import TestClient

from interface import routes as routes_module
from main import app

client = TestClient(app)


def _register_test_agent(monkeypatch) -> str:
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
        json={"agent_secret": "seed", "pow_challenge": "x.y", "pow_nonce": "1"},
    )
    assert reg.status_code == 200
    return reg.json()["bearer_token"]


def test_agent_generate_requires_bearer():
    response = client.post("/api/agent/generate", json={"html": "<h1>x</h1>"})
    assert response.status_code == 401


def test_agent_generate_compress_defaults_to_true(monkeypatch):
    token = _register_test_agent(monkeypatch)

    called = {"value": False}

    def fake_minify(html: str) -> str:
        called["value"] = True
        return html

    monkeypatch.setattr(routes_module, "minify_html", fake_minify)

    response = client.post(
        "/api/agent/generate",
        json={"html": "<h1> x </h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert called["value"] is True


def test_agent_generate_rejects_payload_over_100kb(monkeypatch):
    token = _register_test_agent(monkeypatch)
    huge_html = "a" * (102400 + 1)
    response = client.post(
        "/api/agent/generate",
        json={"html": huge_html},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "100KB" in response.json()["detail"]


def test_agent_generate_success_returns_url_and_size(monkeypatch):
    token = _register_test_agent(monkeypatch)
    response = client.post(
        "/api/agent/generate",
        json={"html": "<h1>Hello Agent</h1>", "domain": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "url" in body
    assert "?d=" in body["url"] and "&s=" in body["url"]
    assert body["url_bytes"] == len(body["url"])


def test_agent_generate_rejects_empty_html(monkeypatch):
    token = _register_test_agent(monkeypatch)
    response = client.post(
        "/api/agent/generate",
        json={"html": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_agent_generate_normalizes_http_domain_to_https(monkeypatch):
    token = _register_test_agent(monkeypatch)
    response = client.post(
        "/api/agent/generate",
        json={"html": "<h1>x</h1>", "domain": "http://mtlminiapps.us"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://mtlminiapps.us/")
