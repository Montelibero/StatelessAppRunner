import pytest
import os
import sqlite3
from fastapi.testclient import TestClient
from app.main import app, VALID_KEYS
import app.db as db_module

client = TestClient(app)

# Use the first valid key for testing
TEST_KEY = list(VALID_KEYS)[0]

@pytest.fixture(autouse=True)
def test_db(monkeypatch, tmp_path):
    """
    Fixture to set up a temporary database for testing.
    This runs automatically for every test in this file.
    """
    # Create a temp file path
    d = tmp_path / "data"
    d.mkdir()
    db_file = d / "test_apps.db"

    # Monkeypatch the DB_PATH in the db module
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))

    # Initialize the DB
    db_module.init_db()

    yield

    # Cleanup is handled by tmp_path, but we can verify file exists if needed
    pass

def test_db_operations():
    """Test direct DB operations"""
    slug = "test-slug"
    html = "<h1>Test App</h1>"

    # Save
    db_module.save_app(slug, html)

    # Get
    app_data = db_module.get_app(slug)
    assert app_data is not None
    assert app_data["slug"] == slug
    assert app_data["html_content"] == html
    assert app_data["created_at"] is not None
    assert app_data["updated_at"] is not None

    # Update
    new_html = "<h2>Updated</h2>"
    db_module.save_app(slug, new_html)
    updated_app = db_module.get_app(slug)
    assert updated_app["html_content"] == new_html
    assert updated_app["updated_at"] >= updated_app["created_at"]

    # List
    apps = db_module.list_apps()
    assert len(apps) == 1
    assert apps[0]["slug"] == slug

    # Delete
    db_module.delete_app(slug)
    assert db_module.get_app(slug) is None
    assert len(db_module.list_apps()) == 0

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
    app_data = db_module.get_app(slug)
    assert app_data["html_content"] == html

def test_api_save_app_invalid_key():
    """Test POST /api/apps with invalid key"""
    response = client.post("/api/apps", json={
        "key": "invalid-key",
        "slug": "fail",
        "html": "..."
    })
    assert response.status_code == 403

def test_api_save_app_empty_slug():
    """Test POST /api/apps with empty slug"""
    response = client.post("/api/apps", json={
        "key": TEST_KEY,
        "slug": "",
        "html": "..."
    })
    assert response.status_code == 400

def test_api_list_apps():
    """Test GET /api/apps"""
    # Create a couple of apps
    db_module.save_app("app1", "c1")
    db_module.save_app("app2", "c2")

    response = client.get("/api/apps")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    slugs = [item["slug"] for item in data]
    assert "app1" in slugs
    assert "app2" in slugs

def test_api_get_app():
    """Test GET /api/apps/{slug}"""
    slug = "get-test"
    db_module.save_app(slug, "content")

    response = client.get(f"/api/apps/{slug}")
    assert response.status_code == 200
    assert response.json()["slug"] == slug
    assert response.json()["html_content"] == "content"

def test_api_get_app_not_found():
    """Test GET /api/apps/{slug} 404"""
    response = client.get("/api/apps/non-existent")
    assert response.status_code == 404

def test_api_delete_app():
    """Test DELETE /api/apps/{slug}"""
    slug = "del-test"
    db_module.save_app(slug, "content")

    response = client.request("DELETE", f"/api/apps/{slug}", json={"key": TEST_KEY})
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    assert db_module.get_app(slug) is None

def test_api_delete_app_invalid_key():
    """Test DELETE /api/apps/{slug} invalid key"""
    slug = "del-secure"
    db_module.save_app(slug, "content")

    response = client.request("DELETE", f"/api/apps/{slug}", json={"key": "bad"})
    assert response.status_code == 403

    # Should still exist
    assert db_module.get_app(slug) is not None

def test_serve_persistent_app():
    """Test GET /p/{slug}"""
    slug = "serve-me"
    html = "<html><body>Hosted App</body></html>"
    db_module.save_app(slug, html)

    response = client.get(f"/p/{slug}")
    assert response.status_code == 200
    assert response.text == html
    assert response.headers["content-type"] == "text/html; charset=utf-8"

def test_serve_persistent_app_404():
    """Test GET /p/{slug} not found"""
    response = client.get("/p/phantom")
    assert response.status_code == 404
