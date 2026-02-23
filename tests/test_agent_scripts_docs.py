from pathlib import Path


def test_skill_md_contains_required_agent_flow():
    text = Path("app/public/skill.md").read_text(encoding="utf-8")
    assert "https://mtlminiapps.us/api/agent/generate" in text
    assert "https://mtlminiapps.us/api/agent/apps" in text
    assert "100KB" in text
    assert "compress" in text and "true" in text.lower()
    assert "7 days" in text or "7 дней" in text
    assert "https://mtlminiapps.us/skill.md" in text
    assert "https://mtlminiapps.us/scripts/register_agent.py" in text
    assert "https://mtlminiapps.us/scripts/register_agent.mjs" in text


def test_llm_txt_contains_required_agent_flow():
    text = Path("app/public/llm.txt").read_text(encoding="utf-8")
    assert "POST https://mtlminiapps.us/api/agent/generate" in text
    assert "POST https://mtlminiapps.us/api/agent/apps" in text
    assert "100KB" in text
    assert "compress" in text and "default true" in text.lower()
    assert "TTL" in text


def test_register_agent_python_script_contains_core_steps():
    text = Path("scripts/register_agent.py").read_text(encoding="utf-8")
    assert "hashlib.sha256" in text
    assert "base64.b32encode" in text
    assert "while True" in text
    assert "/api/agent/register" in text
    assert "bearer_token" in text


def test_register_agent_node_script_contains_core_steps():
    text = Path("scripts/register_agent.mjs").read_text(encoding="utf-8")
    assert "createHash('sha256')" in text
    assert ".toString('base64')" in text or "base32" in text.lower()
    assert "while (true)" in text
    assert "/api/agent/register" in text
    assert "bearer_token" in text
