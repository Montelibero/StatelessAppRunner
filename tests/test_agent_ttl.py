import datetime as dt

from fastapi.testclient import TestClient

import db
from interface import routes as routes_module
from main import app, get_agent_app_ttl_days

client = TestClient(app)


def _register_test_agent(monkeypatch) -> tuple[str, str]:
    agent_id = "ABCDEFGHZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZMTL"

    def fake_validate(secret: str) -> tuple[bool, str]:
        return True, agent_id

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)
    monkeypatch.setattr(
        routes_module,
        "verify_registration_pow",
        lambda *_args, **_kwargs: True,
    )
    reg = client.post(
        "/api/agent/register",
        json={"agent_secret": "seed-ttl", "pow_challenge": "x.y", "pow_nonce": "1"},
    )
    assert reg.status_code == 200
    body = reg.json()
    return body["bearer_token"], body["agent_id"]


def test_ttl_env_default_and_override(monkeypatch):
    monkeypatch.delenv("AGENT_APP_TTL_DAYS", raising=False)
    assert get_agent_app_ttl_days() == 7

    monkeypatch.setenv("AGENT_APP_TTL_DAYS", "3")
    assert get_agent_app_ttl_days() == 3


def test_expired_agent_page_returns_404(monkeypatch):
    token, agent_id = _register_test_agent(monkeypatch)
    create = client.post(
        "/api/agent/apps",
        json={"slug": "ttl-expired", "html": "<h1>ttl</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 200

    conn = db.get_connection()
    old = (dt.datetime.now(dt.UTC) - dt.timedelta(days=8)).isoformat()
    with conn:
        conn.execute(
            "UPDATE agent_apps SET last_accessed_at = ?, updated_at = ? WHERE slug = ?",
            (old, old, "ttl-expired"),
        )

    opened = client.get(f"/a/{agent_id}/ttl-expired")
    assert opened.status_code == 404


def test_successful_open_updates_last_accessed(monkeypatch):
    token, agent_id = _register_test_agent(monkeypatch)
    create = client.post(
        "/api/agent/apps",
        json={"slug": "ttl-live", "html": "<h1>live</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 200

    conn = db.get_connection()
    old = (dt.datetime.now(dt.UTC) - dt.timedelta(days=2)).isoformat()
    with conn:
        conn.execute(
            "UPDATE agent_apps SET last_accessed_at = ? WHERE slug = ?",
            (old, "ttl-live"),
        )

    before = client.get("/api/agent/apps", headers={"Authorization": f"Bearer {token}"})
    before_item = next(item for item in before.json() if item["slug"] == "ttl-live")
    before_ts = before_item["last_accessed_at"]

    opened = client.get(f"/a/{agent_id}/ttl-live")
    assert opened.status_code == 200

    after = client.get("/api/agent/apps", headers={"Authorization": f"Bearer {token}"})
    after_item = next(item for item in after.json() if item["slug"] == "ttl-live")
    assert after_item["last_accessed_at"] >= before_ts


def test_app_not_expired_if_recently_updated(monkeypatch):
    token, agent_id = _register_test_agent(monkeypatch)
    create = client.post(
        "/api/agent/apps",
        json={"slug": "ttl-updated", "html": "<h1>updated</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 200

    conn = db.get_connection()
    # last_accessed_at 10 days ago (expired)
    old_access = (dt.datetime.now(dt.UTC) - dt.timedelta(days=10)).isoformat()
    # updated_at is now (fresh)
    new_update = dt.datetime.now(dt.UTC).isoformat()

    with conn:
        conn.execute(
            "UPDATE agent_apps SET last_accessed_at = ?, updated_at = ? WHERE slug = ?",
            (old_access, new_update, "ttl-updated"),
        )

    # Should be accessible because updated_at is fresh
    opened = client.get(f"/a/{agent_id}/ttl-updated")
    assert opened.status_code == 200
