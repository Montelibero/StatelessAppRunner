from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_homepage_structure():
    response = client.get("/")
    assert response.status_code == 200

    # Check for specific content we added
    assert "Stateless App Runner" in response.text
    assert "Безопасная среда для запуска" in response.text
    assert "View source on GitHub" in response.text
    assert "bulma.min.css" in response.text

    # Check for link to admin
    assert 'href="/admin"' in response.text

    # Check for github link - Updated to match actual file content
    assert 'href="https://github.com/Montelibero/StatelessAppRunner"' in response.text
