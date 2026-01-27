import pytest
from fastapi.testclient import TestClient
from main import app, DEFAULT_SECRET
import db
import uuid

client = TestClient(app)
TEST_KEY = DEFAULT_SECRET

def test_db_operations():
    """Test direct DB operations"""
    slug = "test-slug"
    html = "<h1>Test App</h1>"

    # Save (defaults to Admin user_id=1)
    db.save_app(slug, html)

    # Get
    app_data = db.get_app(slug)
    assert app_data is not None
    assert app_data["slug"] == slug
    assert app_data["html_content"] == html
    assert app_data["user_id"] == 1

    # Update
    new_html = "<h2>Updated</h2>"
    db.save_app(slug, new_html)
    updated_app = db.get_app(slug)
    assert updated_app["html_content"] == new_html

    # List
    apps = db.list_apps()
    assert len(apps) >= 1
    slugs = [a['slug'] for a in apps]
    assert slug in slugs

    # Delete
    db.delete_app(slug)
    assert db.get_app(slug) is None

def test_api_save_app():
    """Test POST /api/apps"""
    slug = "api-test"
    html = "<p>API Content</p>"

    response = client.post("/api/apps", json={
        "key": TEST_KEY,
        "slug": slug,
        "html": html
    })

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["slug"] == slug

    # Verify in DB
    app_data = db.get_app(slug)
    assert app_data["html_content"] == html

def test_api_save_app_invalid_key():
    """Test POST /api/apps with invalid key"""
    response = client.post("/api/apps", json={
        "key": "invalid-key",
        "slug": "fail",
        "html": "..."
    })
    assert response.status_code == 403

def test_api_list_apps():
    """Test GET /api/apps"""
    # Create a couple of apps
    db.save_app("app1", "c1")

    response = client.get(f"/api/apps?key={TEST_KEY}")
    assert response.status_code == 200
    data = response.json()
    slugs = [item["slug"] for item in data]
    assert "app1" in slugs

def test_api_get_app():
    """Test GET /api/apps/{slug}"""
    slug = "get-test"
    db.save_app(slug, "content")

    response = client.get(f"/api/apps/{slug}?key={TEST_KEY}")
    assert response.status_code == 200
    assert response.json()["slug"] == slug
    assert response.json()["html_content"] == "content"

def test_api_delete_app():
    """Test DELETE /api/apps/{slug}"""
    slug = "del-test"
    db.save_app(slug, "content")

    response = client.request("DELETE", f"/api/apps/{slug}", json={"key": TEST_KEY})
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    assert db.get_app(slug) is None

def test_isolation_and_routing():
    # 1. Create User
    ukey = f"mini{uuid.uuid4()}"
    resp = client.post("/api/users", json={
        "admin_key": TEST_KEY,
        "key": ukey,
        "comment": "User 2"
    })
    assert resp.status_code == 200
    uid = resp.json()['id']

    # 2. User saves "game"
    client.post("/api/apps", json={"key": ukey, "slug": "game", "html": "User Game"})

    # 3. Admin saves "game"
    client.post("/api/apps", json={"key": TEST_KEY, "slug": "game", "html": "Admin Game"})

    # 4. Access via /p/...
    # Admin (User 1) -> /p/game
    resp_admin = client.get("/p/game")
    assert resp_admin.status_code == 200
    assert "Admin Game" in resp_admin.text

    # User (User X) -> /pX/game
    resp_user = client.get(f"/p{uid}/game")
    assert resp_user.status_code == 200
    assert "User Game" in resp_user.text

    # 5. Access via API (Get Details)
    # Admin API -> Admin Game
    resp = client.get(f"/api/apps/game?key={TEST_KEY}")
    assert resp.json()['html_content'] == "Admin Game"

    # User API -> User Game
    resp = client.get(f"/api/apps/game?key={ukey}")
    assert resp.json()['html_content'] == "User Game"

def test_admin_management_safety():
    # 1. Create User
    ukey = f"mini{uuid.uuid4()}"
    resp = client.post("/api/users", json={
        "admin_key": TEST_KEY,
        "key": ukey,
        "comment": "User 3"
    })
    uid = resp.json()['id']

    # 2. User 3 saves "tool"
    client.post("/api/apps", json={"key": ukey, "slug": "tool", "html": "User Tool"})

    # 3. Admin saves "tool" (Collision)
    client.post("/api/apps", json={"key": TEST_KEY, "slug": "tool", "html": "Admin Tool"})

    # 4. Admin deletes User 3's "tool" specifically
    # Should use ?target_user_id=uid
    resp = client.request("DELETE", f"/api/apps/tool?target_user_id={uid}", json={"key": TEST_KEY})
    assert resp.status_code == 200

    # Verify User 3's tool is gone
    app_u3 = db.get_app("tool", user_id=uid)
    assert app_u3 is None

    # Verify Admin's tool is STILL THERE
    app_admin = db.get_app("tool", user_id=1)
    assert app_admin is not None
    assert app_admin['html_content'] == "Admin Tool"

    # 5. Admin saves FOR User 3 (Create new)
    client.post("/api/apps", json={
        "key": TEST_KEY,
        "slug": "tool",
        "html": "Admin Created for User 3",
        "owner_id": uid
    })

    # Verify User 3 has it
    app_u3_new = db.get_app("tool", user_id=uid)
    assert app_u3_new is not None
    assert app_u3_new['html_content'] == "Admin Created for User 3"

    # Verify Admin's tool is UNTOUCHED
    app_admin = db.get_app("tool", user_id=1)
    assert app_admin['html_content'] == "Admin Tool"

    # 6. Admin GET User 3's app explicitly
    resp = client.get(f"/api/apps/tool?key={TEST_KEY}&target_user_id={uid}")
    assert resp.status_code == 200
    assert resp.json()['html_content'] == "Admin Created for User 3"
