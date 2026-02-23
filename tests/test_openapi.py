from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_openapi_excludes_admin_and_ui_routes():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = set(response.json().get("paths", {}).keys())

    # Must not expose admin/internal UI surface.
    forbidden = {
        "/",
        "/admin",
        "/admin/fragments/apps",
        "/admin/fragments/apps/save",
        "/admin/fragments/users",
        "/admin/fragments/users/create",
        "/admin/fragments/agents",
        "/admin/fragments/agents/apps",
        "/admin/fragments/agents/toggle",
        "/p/{slug}",
        "/p{user_id}/{slug}",
        "/a/{agent_id}/{slug}",
        "/skill.md",
        "/llm.txt",
        "/scripts/register_agent.py",
        "/scripts/register_agent.mjs",
        "/api/users",
    }
    assert not (paths & forbidden)

    # External API routes should stay documented.
    required = {
        "/api/agent/register/challenge",
        "/api/agent/register",
        "/api/agent/me",
        "/api/agent/generate",
        "/api/agent/apps",
        "/api/agent/apps/{slug}",
        "/api/generate",
        "/api/apps",
        "/api/apps/{slug}",
    }
    assert required.issubset(paths)
