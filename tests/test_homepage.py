from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_homepage_structure():
    response = client.get("/")
    assert response.status_code == 200

    # Agent-first homepage content
    assert "Stateless App Runner" in response.text
    assert "Если вы агент" in response.text
    assert "Если вы человек" in response.text
    assert "Передайте ссылку на этот сервис вашему AI-агенту" in response.text
    assert 'href="/skill.md"' in response.text
    assert 'href="/scripts/register_agent.py"' in response.text
    assert 'href="/scripts/register_agent.mjs"' in response.text
    assert "View source on GitHub" in response.text
    assert "bulma.min.css" in response.text

    # No admin link in public homepage
    assert 'href="/admin"' not in response.text

    # Check for github link - Updated to match actual file content
    assert 'href="https://github.com/Montelibero/StatelessAppRunner"' in response.text
