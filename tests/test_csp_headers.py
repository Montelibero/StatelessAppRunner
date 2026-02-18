from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_security_headers():
    paths = ["/", "/admin"]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200

        # Check CSP
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self' https://unpkg.com https://cdn.jsdelivr.net 'unsafe-inline'" in csp
        assert "style-src 'self' https://cdn.jsdelivr.net https://unpkg.com 'unsafe-inline'" in csp
        assert "frame-ancestors 'self'" in csp

        # Check other headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_security_headers_on_error():
    # Middleware should apply even on errors (e.g. 404 or 403)
    response = client.get("/non-existent-page")
    assert response.status_code == 404
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
