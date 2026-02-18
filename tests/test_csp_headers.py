from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_security_headers_system_routes():
    # Strict headers for system pages
    paths = ["/", "/admin"]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200

        # Check CSP (Strict)
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self' https://unpkg.com https://cdn.jsdelivr.net 'unsafe-inline'" in csp

        # Check X-Frame-Options (Strict)
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"

        # General headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_security_headers_runner_routes():
    # Permissive headers for runner routes
    # Mocking a signed URL (signature doesn't matter for middleware path logic, but let's be realistic)
    response = client.get("/?d=payload&s=signature")
    # Note: run_app will fail signature check and return 403, but middleware applies to response
    assert response.status_code == 403

    # Check CSP (Permissive)
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "default-src *" in csp
    assert "'unsafe-eval'" in csp
    assert "frame-ancestors *" in csp

    # X-Frame-Options should NOT be SAMEORIGIN (it might be absent or different)
    assert response.headers.get("X-Frame-Options") != "SAMEORIGIN"

def test_security_headers_persistent_routes():
    # Permissive headers for /p routes
    response = client.get("/p/some-slug")
    # Will be 404 if not found, but middleware still applies
    assert response.status_code == 404

    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "default-src *" in csp
    assert "frame-ancestors *" in csp

    assert response.headers.get("X-Frame-Options") != "SAMEORIGIN"
