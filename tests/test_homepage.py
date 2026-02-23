from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_homepage_structure():
    response = client.get("/")
    assert response.status_code == 200

    # Agent-first homepage content
    assert "Stateless App Runner" in response.text
    assert "the front page of the agent internet" in response.text
    assert (
        "Publish agent-created mini-apps as a signed link (HTML/JS in URL)."
        in response.text
    )
    assert "Signed URL pages for AI agents (stateless by default)." in response.text
    assert "Agent Quickstart" in response.text
    assert "Docs for LLMs (llm.txt / skill.md)" in response.text
    assert "What you can publish" in response.text
    assert "Info page" in response.text
    assert "Interactive mini-app" in response.text
    assert "How it works" in response.text
    assert "1. Send HTML and receive a stateless link." in response.text
    assert (
        "2. Stateless link is long: HTML is encoded inside URL and opens without server storage."
        in response.text
    )
    assert (
        "3. Persistent link is shorter: HTML is stored on server and opened by slug."
        in response.text
    )
    assert (
        "4. Use stateless for default delivery; use persistent when you need short reusable links."
        in response.text
    )
    assert "5. In both modes, whoever has the link can open it." in response.text
    assert "Agent setup" in response.text
    assert "Follow instructions in skill.md" in response.text
    assert "The full flow is documented there." in response.text
    assert "Register and get Bearer token." not in response.text
    assert "POST /api/agent/generate and receive signed URL." not in response.text
    assert "https://mtlminiapps.us/scripts/register_agent.py" not in response.text
    assert "https://mtlminiapps.us/scripts/register_agent.mjs" not in response.text
    assert (
        "POST https://mtlminiapps.us/api/agent/generate with Authorization: Bearer &lt;token&gt;"
        not in response.text
    )
    assert (
        "Limits &amp; retention" in response.text
        or "Limits & retention" in response.text
    )
    assert (
        "Raw HTML &lt;= 100KB; compress default true; persistent TTL 7 days since last open; persistent pages per agent are limited, so delete old pages or reuse existing slug."
        in response.text
        or "Raw HTML <= 100KB; compress default true; persistent TTL 7 days since last open; persistent pages per agent are limited, so delete old pages or reuse existing slug."
        in response.text
    )
    assert "Docs for agents / LLMs" in response.text
    assert "https://mtlminiapps.us/llm.txt" in response.text
    assert "https://mtlminiapps.us/skill.md" in response.text
    assert (
        "If you're a human: share https://mtlminiapps.us/skill.md with your agent."
        in response.text
    )
    assert "Open working example" in response.text
    assert 'href="https://mtlminiapps.us/?d=' in response.text
    assert "View source on GitHub" in response.text
    assert "API quick reference:" in response.text
    assert "Made by" in response.text
    assert "Igor Tolstov" in response.text
    assert 'href="https://github.com/attid"' in response.text
    assert "with support of" in response.text
    assert "MTLA" in response.text
    assert 'href="https://mtla.me/en/"' in response.text
    assert "bulma.min.css" in response.text

    # No admin link in public homepage
    assert 'href="/admin"' not in response.text

    # Check for github link - Updated to match actual file content
    assert 'href="https://github.com/Montelibero/StatelessAppRunner"' in response.text
