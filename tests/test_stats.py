import pytest
from fastapi.testclient import TestClient
from main import app, DEFAULT_SECRET, sign_data, compress_payload
import db
import uuid

client = TestClient(app)
TEST_KEY = DEFAULT_SECRET

def test_stats_tracking():
    # 1. Create User
    ukey = f"mini{uuid.uuid4()}"
    resp = client.post("/api/users", json={
        "admin_key": TEST_KEY,
        "key": ukey,
        "comment": "Stats User"
    })
    uid = resp.json()['id']

    # 2. User generates a link (Stateless Generate)
    html = "<h1>Stateless</h1>"
    resp = client.post("/api/generate", json={
        "key": ukey,
        "html": html,
        "compress": False
    })
    url = resp.json()['url']

    # 3. User views the stateless link (Stateless View)
    query_string = url.split("?")[1]
    client.get(f"/?{query_string}")

    # 4. User saves an app (App Count)
    client.post("/api/apps", json={"key": ukey, "slug": "stat-app", "html": "Persistent"})

    # 5. User views the app (Persistent View)
    client.get(f"/p{uid}/stat-app")

    # 6. Verify Stats via Admin API
    resp = client.get(f"/api/users?key={TEST_KEY}")
    users = resp.json()

    target_user = next(u for u in users if u['id'] == uid)
    stats = target_user['stats']

    print(f"Stats for User {uid}: {stats}")

    assert stats['generated'] == 1
    assert stats['view_stateless'] == 1
    assert stats['apps_count'] == 1
    assert stats['view_persistent'] == 1

def test_stats_view_stateless_attribution():
    # Ensure view is attributed to the KEY OWNER, not necessarily who viewed it (since viewer is anonymous)
    # 1. Create User A
    key_a = f"mini{uuid.uuid4()}"
    client.post("/api/users", json={"admin_key": TEST_KEY, "key": key_a, "comment": "A"})

    # 2. User A generates link
    payload = compress_payload("Test")
    sig = sign_data(payload, key_a)

    # 3. Anonymous view
    client.get(f"/?d={payload}&s={sig}")

    # 4. Verify User A got the view count
    resp = client.get(f"/api/users?key={TEST_KEY}")
    target = next(u for u in resp.json() if u['key'] == key_a)
    assert target['stats']['view_stateless'] == 1

def test_stats_view_persistent_admin():
    # Admin view counts too
    client.post("/api/apps", json={"key": TEST_KEY, "slug": "admin-stat", "html": "Admin App"})
    client.get("/p/admin-stat")

    resp = client.get(f"/api/users?key={TEST_KEY}")
    admin = next(u for u in resp.json() if u['id'] == 1)

    # We don't know initial state (test pollution?), so check > 0
    assert admin['stats']['view_persistent'] >= 1
    assert admin['stats']['apps_count'] >= 1
