from ui.pages import (
    render_admin_page,
    render_apps_fragment,
    render_home_page,
    render_users_fragment,
)


def test_render_home_page_contains_core_markers():
    html = render_home_page()
    assert "Stateless App Runner" in html
    assert "bulma.min.css" in html
    assert "Если вы агент" in html
    assert "Если вы человек" in html
    assert "Передайте ссылку на этот сервис вашему AI-агенту" in html
    assert 'href="/skill.md"' in html
    assert 'href="/scripts/register_agent.py"' in html
    assert 'href="/scripts/register_agent.mjs"' in html
    assert 'href="/admin"' not in html
    assert "View source on GitHub" in html


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
    assert "/admin/fragments/apps" in html
    assert "/admin/fragments/users" in html
    assert 'id="len-info"' in html
    assert 'id="limit-bar"' in html
    assert "innerHTML =" not in html
    assert 'const fullKey = "mini" + uuidPart;' not in html


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
