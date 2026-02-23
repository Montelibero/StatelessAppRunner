import re

from fastapi.testclient import TestClient

from interface import routes as routes_module
from main import app

client = TestClient(app)


def _register_test_agent(monkeypatch) -> tuple[str, str]:
    agent_id = "ABCDEFGHZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZMTL"

    def fake_validate(secret: str) -> tuple[bool, str]:
        return True, agent_id

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)
    reg = client.post("/api/agent/register", json={"agent_secret": "seed"})
    assert reg.status_code == 200
    body = reg.json()
    return body["bearer_token"], body["agent_id"]


def test_agent_apps_create_with_auto_slug(monkeypatch):
    token, agent_id = _register_test_agent(monkeypatch)
    response = client.post(
        "/api/agent/apps",
        json={"html": "<h1>auto</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert re.fullmatch(r"[a-z0-9]{8}", body["slug"])
    assert body["url"].endswith(f"/a/{agent_id}/{body['slug']}")


def test_agent_apps_create_list_open_and_delete(monkeypatch):
    token, agent_id = _register_test_agent(monkeypatch)
    slug = "demoagent"

    create = client.post(
        "/api/agent/apps",
        json={"slug": slug, "html": "<h1>persistent</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 200
    assert create.json()["slug"] == slug

    listed = client.get("/api/agent/apps", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert any(item["slug"] == slug for item in listed.json())

    opened = client.get(f"/a/{agent_id}/{slug}")
    assert opened.status_code == 200
    assert "persistent" in opened.text

    deleted = client.delete(
        f"/api/agent/apps/{slug}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200

    opened_after_delete = client.get(f"/a/{agent_id}/{slug}")
    assert opened_after_delete.status_code == 404


def test_agent_apps_reject_over_100kb(monkeypatch):
    token, _ = _register_test_agent(monkeypatch)
    huge_html = "x" * (102400 + 1)
    response = client.post(
        "/api/agent/apps",
        json={"html": huge_html},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "100KB" in response.json()["detail"]
