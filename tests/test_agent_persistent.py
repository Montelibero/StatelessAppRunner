import re
import datetime as dt

from fastapi.testclient import TestClient

import db
from interface import routes as routes_module
from main import app

client = TestClient(app)


def _register_test_agent(monkeypatch) -> tuple[str, str, int]:
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
        json={"agent_secret": "seed", "pow_challenge": "x.y", "pow_nonce": "1"},
    )
    assert reg.status_code == 200
    body = reg.json()
    token = body["bearer_token"]
    me = client.get("/api/agent/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, body["agent_id"], int(me.json()["id"])


def test_agent_apps_create_with_auto_slug(monkeypatch):
    token, agent_id, _ = _register_test_agent(monkeypatch)
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
    token, agent_id, _ = _register_test_agent(monkeypatch)
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
    token, _, _ = _register_test_agent(monkeypatch)
    huge_html = "x" * (102400 + 1)
    response = client.post(
        "/api/agent/apps",
        json={"html": huge_html},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "100KB" in response.json()["detail"]


def test_agent_apps_reject_empty_html(monkeypatch):
    token, _, _ = _register_test_agent(monkeypatch)
    response = client.post(
        "/api/agent/apps",
        json={"slug": "empty", "html": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_agent_apps_limit_total_count(monkeypatch):
    token, _, agent_ref_id = _register_test_agent(monkeypatch)
    conn = db.get_connection()
    old = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=2)).isoformat()
    with conn:
        for i in range(80):
            conn.execute(
                """
                INSERT INTO agent_apps (
                    agent_ref_id, slug, html_content, content_encoding, created_at, updated_at, last_accessed_at
                ) VALUES (?, ?, ?, 'gzip', ?, ?, ?)
                """,
                (agent_ref_id, f"s{i}", b"x", old, old, old),
            )

    blocked = client.post(
        "/api/agent/apps",
        json={"slug": "overflow", "html": "<h1>x</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 409
    assert "limit" in blocked.json()["detail"].lower()


def test_agent_apps_hourly_create_rate_limit(monkeypatch):
    token, _, agent_ref_id = _register_test_agent(monkeypatch)
    conn = db.get_connection()
    ts = (dt.datetime.now(dt.UTC) - dt.timedelta(minutes=10)).isoformat()
    with conn:
        for i in range(20):
            conn.execute(
                """
                INSERT INTO agent_access_logs (agent_ref_id, action, slug, timestamp)
                VALUES (?, 'create_persistent', ?, ?)
                """,
                (agent_ref_id, f"h{i}", ts),
            )

    blocked = client.post(
        "/api/agent/apps",
        json={"slug": "h-over", "html": "<h1>x</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 429


def test_agent_apps_daily_create_rate_limit(monkeypatch):
    token, _, agent_ref_id = _register_test_agent(monkeypatch)
    conn = db.get_connection()
    now = dt.datetime.now(dt.UTC)
    day_start = now - dt.timedelta(hours=23)
    old_hour = now - dt.timedelta(hours=2)

    for i in range(40):
        created = day_start if i < 20 else old_hour
        with conn:
            conn.execute(
                """
                INSERT INTO agent_apps (
                    agent_ref_id, slug, html_content, content_encoding, created_at, updated_at, last_accessed_at
                )
                VALUES (?, ?, ?, 'gzip', ?, ?, ?)
                """,
                (
                    agent_ref_id,
                    f"d{i}",
                    b"x",
                    created.isoformat(),
                    created.isoformat(),
                    created.isoformat(),
                ),
            )
            conn.execute(
                """
                INSERT INTO agent_access_logs (agent_ref_id, action, slug, timestamp)
                VALUES (?, 'create_persistent', ?, ?)
                """,
                (agent_ref_id, f"d{i}", created.isoformat()),
            )

    blocked = client.post(
        "/api/agent/apps",
        json={"slug": "d-over", "html": "<h1>x</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 429


def test_agent_apps_edit_existing_slug_not_rate_limited(monkeypatch):
    token, _, agent_ref_id = _register_test_agent(monkeypatch)
    created = client.post(
        "/api/agent/apps",
        json={"slug": "edit-me", "html": "<h1>v1</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 200

    conn = db.get_connection()
    now = dt.datetime.now(dt.UTC)
    with conn:
        for i in range(20):
            conn.execute(
                """
                INSERT INTO agent_access_logs (agent_ref_id, action, slug, timestamp)
                VALUES (?, 'create_persistent', ?, ?)
                """,
                (agent_ref_id, f"f{i}", now.isoformat()),
            )

    updated = client.post(
        "/api/agent/apps",
        json={"slug": "edit-me", "html": "<h1>v2</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert updated.status_code == 200


def test_agent_apps_edit_rate_limited_per_minute(monkeypatch):
    token, _, agent_ref_id = _register_test_agent(monkeypatch)
    created = client.post(
        "/api/agent/apps",
        json={"slug": "edit-rate", "html": "<h1>v1</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 200

    conn = db.get_connection()
    now = dt.datetime.now(dt.UTC).isoformat()
    with conn:
        for i in range(5):
            conn.execute(
                """
                INSERT INTO agent_access_logs (agent_ref_id, action, slug, timestamp)
                VALUES (?, 'update_persistent', ?, ?)
                """,
                (agent_ref_id, f"u{i}", now),
            )

    blocked = client.post(
        "/api/agent/apps",
        json={"slug": "edit-rate", "html": "<h1>v2</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 429
