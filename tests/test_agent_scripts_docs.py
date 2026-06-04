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
    assert "Do not ask user to provide `agent_secret`." in text
    assert "`pow_nonce`" in text
    assert "`pow_nonce` (string)" in text
    assert "`agent_name` (optional string)" in text
    assert "`client` (optional string" in text
    assert "non-empty UTF-8 string" in text
    assert "domain` overrides returned link host" in text
    assert "Persistent pages per agent are limited." in text
    assert "reusing existing `slug`" in text
    assert "Content-Type: application/json" in text
    assert "max `5` per minute" in text
    assert "max `20` per hour" in text
    assert "max `40` per day" in text
    assert "max `80`" in text


def test_llm_txt_contains_required_agent_flow():
    text = Path("app/public/llm.txt").read_text(encoding="utf-8")
    assert "POST https://mtlminiapps.us/api/agent/generate" in text
    assert "POST https://mtlminiapps.us/api/agent/apps" in text
    assert "100KB" in text
    assert "compress" in text and "default true" in text.lower()
    assert "TTL" in text
    assert "Do not ask user for `agent_secret`" in text
    assert "`pow_nonce`" in text
    assert "pow_nonce` must be string" in text
    assert "Optional register fields: `agent_name`" in text
    assert "domain: overrides returned link host" in text
    assert "Persistent pages per agent are limited." in text
    assert "reusing existing slug" in text
    assert "Content-Type: application/json" in text
    assert "5/min" in text
    assert "20/hour" in text
    assert "40/day" in text
    assert "80" in text
    assert "compress defaults to false for https://mtlminiapps.us/api/generate" in text


def test_register_agent_python_script_contains_core_steps():
    text = Path("app/public/skill/scripts/register_agent.py").read_text(encoding="utf-8")
    assert "hashlib.sha256" in text
    assert "base64.b32encode" in text
    assert "while True" in text
    assert "/api/agent/register" in text
    assert "pow_nonce" in text
    assert "bearer_token" in text


def test_register_agent_node_script_contains_core_steps():
    text = Path("app/public/skill/scripts/register_agent.mjs").read_text(encoding="utf-8")
    assert "createHash('sha256')" in text
    assert ".toString('base64')" in text or "base32" in text.lower()
    assert "while (true)" in text
    assert "/api/agent/register" in text
    assert "pow_nonce" in text
    assert "bearer_token" in text
