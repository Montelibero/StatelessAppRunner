from ui.pages import (
    render_agents_fragment,
    render_admin_page,
    render_apps_fragment,
    render_home_page,
    render_terms_page,
    render_users_fragment,
)


def test_render_home_page_contains_core_markers():
    html = render_home_page()
    assert "Stateless App Runner" in html
    assert "bulma.min.css" in html
    assert "the front page of the agent internet" in html
    assert (
        "Publish agent-created pages as links: stateless (HTML in URL) or persistent (HTML on server)."
        in html
    )
    assert "Stateless mode is default." in html
    assert "Read skill.md" in html
    assert "Docs for LLMs (llm.txt / skill.md)" in html
    assert "What you can publish" in html
    assert "Info page" in html
    assert "Interactive mini-app" in html
    assert "How it works" in html
    assert "1. You send HTML payload to this service." in html
    assert (
        "2. Stateless output: long signed URL with HTML in the URL; page HTML is not stored on server."
        in html
    )
    assert (
        "3. Persistent output: shorter URL /a/{agent_id}/{slug}; page HTML is stored on server."
        in html
    )
    assert (
        "4. Persistent pages expire after 7 days since last successful open (AGENT_APP_TTL_DAYS)."
        in html
    )
    assert "5. In both modes, anyone with the link can open it." in html
    assert "Agent setup" in html
    assert "For registration and API usage, follow only skill.md" in html
    assert "This page intentionally omits registration details." in html
    assert "Register and get Bearer token." not in html
    assert "POST /api/agent/generate and receive signed URL." not in html
    assert "https://mtlminiapps.us/scripts/register_agent.py" not in html
    assert "https://mtlminiapps.us/scripts/register_agent.mjs" not in html
    assert (
        "POST https://mtlminiapps.us/api/agent/generate with Authorization: Bearer &lt;token&gt;"
        not in html
    )
    assert "Limits &amp; retention" in html
    assert (
        "Raw HTML payload limit is 100KB per request. In /api/agent/generate, compress defaults to true. Persistent pages expire after 7 days since last successful open. Persistent pages per agent are limited, so delete old pages or reuse an existing slug."
        in html
    )
    assert "Docs for agents / LLMs" in html
    assert "https://mtlminiapps.us/skill.md" in html
    assert "https://mtlminiapps.us/llm.txt" in html
    assert (
        "If you're a human: share https://mtlminiapps.us/skill.md with your agent."
        in html
    )
    assert "Install as a skill" in html
    assert 'href="/skill.zip"' in html
    assert "Open working example" in html
    assert 'href="https://mtlminiapps.us/?d=' in html
    assert 'href="/admin"' not in html
    assert "View source on GitHub" in html
    assert "API quick reference:" in html
    assert "By using this service, you agree to the" in html
    assert 'href="/terms"' in html
    assert "Made by" in html
    assert "Igor Tolstov" in html
    assert 'href="https://github.com/attid"' in html
    assert "with support of" in html
    assert "MTLA" in html
    assert 'href="https://mtla.me/en/"' in html


def test_render_admin_page_contains_core_markers():
    html = render_admin_page()
    assert "Генератор ссылок" in html
    assert "bulma.min.css" in html
    assert "htmx.org" in html
    assert 'id="generate-btn"' in html
    assert 'id="advanced-btn"' in html
    assert 'id="advanced-panel"' in html
    assert 'id="tab-users"' in html
    assert 'id="content-saved"' in html
    assert 'id="users-list"' in html
    assert 'id="tab-agents"' in html
    assert 'id="content-agents"' in html
    assert 'id="agents-list"' in html
    assert "/admin/fragments/apps" in html
    assert "/admin/fragments/users" in html
    assert "/admin/fragments/agents" in html
    assert 'id="len-info"' in html
    assert 'id="limit-bar"' in html
    assert "innerHTML =" not in html
    assert 'const fullKey = "mini" + uuidPart;' not in html


def test_render_terms_page_contains_core_markers():
    html = render_terms_page()
    assert "Terms" in html
    assert 'provided on an "as is" and "as available" basis' in html
    assert "Data may be deleted" in html
    assert "Prohibited uses include illegal activity, spam, fraud" in html
    assert "By using this service, you agree to these Terms." in html


def test_render_pages_do_not_read_template_files(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("UI renderer should not read template files from disk")

    monkeypatch.setattr("builtins.open", fail_open)

    home_html = render_home_page()
    admin_html = render_admin_page()

    assert "Stateless App Runner" in home_html
    assert "Генератор ссылок" in admin_html


def test_render_apps_fragment_states():
    assert "has-text-danger" in render_apps_fragment(error="Ошибка")
    assert "Введите ключ" in render_apps_fragment(info="Введите ключ")
    assert "Список пуст" in render_apps_fragment([])

    html = render_apps_fragment([{"slug": "demo", "user_id": 1, "html_bytes": 123}])
    assert "demo" in html
    assert "/p/demo" in html
    assert "123 B" in html

    html_user = render_apps_fragment(
        [{"slug": "demo2", "user_id": 7, "html_bytes": 456}]
    )
    assert "/p7/demo2" in html_user
    assert "456 B" in html_user


def test_render_users_fragment_states():
    assert "has-text-danger" in render_users_fragment(error="Ошибка")
    assert "Введите admin ключ" in render_users_fragment(info="Введите admin ключ")
    assert "пуст" in render_users_fragment([])

    html = render_users_fragment(
        [
            {
                "id": 5,
                "key": "mini_abc",
                "comment": "QA",
                "stats": {
                    "generated": 1,
                    "view_stateless": 2,
                    "view_persistent": 3,
                    "apps_count": 4,
                },
            }
        ]
    )
    assert "Список пользователей" in html
    assert "mini_abc" in html
    assert "View /p 3" in html


def test_render_agents_fragment_states():
    assert "has-text-danger" in render_agents_fragment(error="Ошибка")
    assert "Введите admin ключ" in render_agents_fragment(info="Введите admin ключ")
    assert "пуст" in render_agents_fragment([])

    html = render_agents_fragment(
        [
            {
                "id": 1,
                "agent_id": "MTLAAAAAZZZ",
                "name": "agent-1",
                "apps_count": 2,
                "tokens_count": 3,
                "last_seen_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    assert "Список агентов" in html
    assert "agent-1" in html
    assert "Apps 2" in html
    assert "Tokens 3" in html
