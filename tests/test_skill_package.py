import io
import zipfile

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_skill_md_folder_route_has_frontmatter():
    response = client.get("/skill/SKILL.md")
    assert response.status_code == 200
    assert response.text.startswith("---\n")
    assert "name: stateless-app-runner" in response.text
    assert "description:" in response.text


def test_skill_scripts_routes_available():
    py = client.get("/skill/scripts/register_agent.py")
    mjs = client.get("/skill/scripts/register_agent.mjs")
    assert py.status_code == 200
    assert mjs.status_code == 200
    assert "python" in py.text.lower()
    assert "node" in mjs.text.lower() or "mjs" in mjs.text.lower()


def test_skill_references_llm_txt_available():
    response = client.get("/skill/references/llm.txt")
    assert response.status_code == 200
    assert "POST https://mtlminiapps.us/api/agent/generate" in response.text


def test_skill_folder_script_matches_legacy_route():
    legacy = client.get("/scripts/register_agent.py")
    packaged = client.get("/skill/scripts/register_agent.py")
    assert legacy.status_code == 200 and packaged.status_code == 200
    assert legacy.text == packaged.text


def test_skill_zip_downloads():
    response = client.get("/skill.zip")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers.get("content-disposition", "")


def test_skill_zip_contains_skill_files():
    response = client.get("/skill.zip")
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "SKILL.md" in names
    assert "scripts/register_agent.py" in names
    assert "scripts/register_agent.mjs" in names
    assert "references/llm.txt" in names
    assert archive.read("SKILL.md").decode("utf-8").startswith("---\n")
