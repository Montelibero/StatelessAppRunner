from fastapi.testclient import TestClient
from main import app, DEFAULT_SECRET
from interface import routes as routes_module

client = TestClient(app)


def test_admin_page():
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Генератор ссылок" in response.text
    assert "tab-agents" in response.text


def test_generation_and_execution_flow():
    html_source = "<h1>Hello Test</h1>"

    # 1. Генерируем ссылку через API
    gen_response = client.post(
        "/api/generate", json={"domain": "", "key": DEFAULT_SECRET, "html": html_source}
    )
    assert gen_response.status_code == 200
    url = gen_response.json()["url"]

    # Парсим параметры из URL (имитация)
    # url будет вида /?d=...&s=...
    query_string = url.split("?")[1]

    # 2. Пытаемся открыть "страницу"
    run_response = client.get(f"/?{query_string}")

    assert run_response.status_code == 200
    assert run_response.text == html_source
    assert run_response.headers["content-type"] == "text/html; charset=utf-8"


def test_bad_signature():
    # Берем валидный payload, но ломаем подпись
    response = client.get("/?d=SGVsbG8=&s=FAKE_SIGNATURE")
    assert response.status_code == 403
    assert "Integrity Check Failed" in response.json()["detail"]


def test_garbage_data():
    # Берем валидную подпись (технически), но мусор вместо данных (сложно сделать без ключа, но допустим)
    # Проще просто отправить мусор
    response = client.get("/?d=NOT_BASE64&s=123")
    # Тут либо 403 (подпись не сойдется), либо 400 (декод упадет)
    # Скорее всего 403, так как HMAC считается от d.
    assert response.status_code == 403


def test_admin_ui_does_not_force_mini_prefix_for_new_user_key():
    response = client.get("/admin")
    assert response.status_code == 200
    # User-provided key should be sent as-is, without forced "mini" prefix.
    assert 'const fullKey = "mini" + uuidPart;' not in response.text


def test_admin_apps_fragment_requires_key():
    response = client.get("/admin/fragments/apps")
    assert response.status_code == 200
    assert "Введите ключ" in response.text


def test_admin_users_fragment_requires_admin_key():
    response = client.get("/admin/fragments/users")
    assert response.status_code == 200
    assert "Введите admin ключ" in response.text


def test_admin_agents_fragment_requires_admin_key():
    response = client.get("/admin/fragments/agents")
    assert response.status_code == 200
    assert "Введите admin ключ" in response.text


def test_admin_users_fragment_with_admin_key():
    response = client.get(f"/admin/fragments/users?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "Список пользователей" in response.text


def test_admin_agents_fragment_with_admin_key():
    response = client.get(f"/admin/fragments/agents?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "Список агентов" in response.text or "пуст" in response.text


def test_admin_apps_fragment_with_invalid_key():
    response = client.get("/admin/fragments/apps?key=bad-key")
    assert response.status_code == 200
    assert "Неверный ключ" in response.text


def test_admin_apps_fragment_with_valid_key():
    response = client.get(f"/admin/fragments/apps?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "Список пуст" in response.text


def test_admin_apps_save_fragment_validation_and_success():
    no_slug = client.post(
        "/admin/fragments/apps/save",
        data={"key": DEFAULT_SECRET, "slug": " ", "html": "<h1>x</h1>"},
    )
    assert no_slug.status_code == 200
    assert "Нужно имя ссылки" in no_slug.text

    ok = client.post(
        "/admin/fragments/apps/save",
        data={"key": DEFAULT_SECRET, "slug": "frag-demo", "html": "<h1>x</h1>"},
    )
    assert ok.status_code == 200
    assert "frag-demo" in ok.text


def test_admin_users_fragment_with_non_admin_key():
    created = client.post(
        "/api/users",
        json={"admin_key": DEFAULT_SECRET, "key": "mini-non-admin", "comment": "u"},
    )
    assert created.status_code == 200

    response = client.get("/admin/fragments/users?key=mini-non-admin")
    assert response.status_code == 200
    assert "Только admin может видеть пользователей" in response.text


def test_admin_agents_fragment_with_non_admin_key():
    created = client.post(
        "/api/users",
        json={"admin_key": DEFAULT_SECRET, "key": "mini-non-admin-2", "comment": "u"},
    )
    assert created.status_code == 200

    response = client.get("/admin/fragments/agents?key=mini-non-admin-2")
    assert response.status_code == 200
    assert "Только admin может видеть агентов" in response.text


def test_admin_agents_fragment_renders_registered_agent(monkeypatch):
    def fake_validate(secret: str) -> tuple[bool, str]:
        return True, "MTLAAAAAZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)
    monkeypatch.setattr(
        routes_module,
        "verify_registration_pow",
        lambda *_args, **_kwargs: True,
    )
    reg = client.post(
        "/api/agent/register",
        json={
            "agent_secret": "seed-admin-agent",
            "pow_challenge": "x.y",
            "pow_nonce": "1",
            "agent_name": "admin-agent",
        },
    )
    assert reg.status_code == 200

    response = client.get(f"/admin/fragments/agents?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "admin-agent" in response.text


def _register_agent_for_admin_tests(monkeypatch, *, secret: str, name: str):
    def fake_validate(_secret: str) -> tuple[bool, str]:
        return True, "MTLAAAAAZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"

    monkeypatch.setattr(routes_module, "validate_agent_secret", fake_validate)
    monkeypatch.setattr(
        routes_module,
        "verify_registration_pow",
        lambda *_args, **_kwargs: True,
    )
    reg = client.post(
        "/api/agent/register",
        json={
            "agent_secret": secret,
            "pow_challenge": "x.y",
            "pow_nonce": "1",
            "agent_name": name,
        },
    )
    assert reg.status_code == 200
    token = reg.json()["bearer_token"]
    me = client.get("/api/agent/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return token, me.json()["id"], me.json()["agent_id"]


def test_admin_agents_pages_fragment_lists_agent_pages(monkeypatch):
    token, agent_ref_id, _ = _register_agent_for_admin_tests(
        monkeypatch, secret="seed-pages", name="pages-agent"
    )
    created = client.post(
        "/api/agent/apps",
        json={"slug": "agent-page-1", "html": "<h1>agent page</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 200

    response = client.get(
        f"/admin/fragments/agents/apps?key={DEFAULT_SECRET}&agent_ref_id={agent_ref_id}"
    )
    assert response.status_code == 200
    assert "agent-page-1" in response.text


def test_admin_agents_fragment_shows_agent_stats(monkeypatch):
    token, _, _ = _register_agent_for_admin_tests(
        monkeypatch, secret="seed-stats", name="stats-agent"
    )
    generated = client.post(
        "/api/agent/generate",
        json={"html": "<h1>stateless</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert generated.status_code == 200
    url = generated.json()["url"]
    query = url.split("?", 1)[1]
    opened = client.get(f"/?{query}")
    assert opened.status_code == 200

    saved = client.post(
        "/api/agent/apps",
        json={"slug": "stats-persist", "html": "<h1>persist</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert saved.status_code == 200

    response = client.get(f"/admin/fragments/agents?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "stats-agent" in response.text
    assert "Gen URL 1" in response.text
    assert "View URL 1" in response.text
    assert "Persist 1" in response.text


def test_admin_ban_agent_kills_persistent_and_stateless_links(monkeypatch):
    token, agent_ref_id, agent_id = _register_agent_for_admin_tests(
        monkeypatch, secret="seed-ban", name="ban-agent"
    )
    persisted = client.post(
        "/api/agent/apps",
        json={"slug": "ban-page", "html": "<h1>persist</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert persisted.status_code == 200

    generated = client.post(
        "/api/agent/generate",
        json={"html": "<h1>stateless</h1>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert generated.status_code == 200
    stateless_query = generated.json()["url"].split("?", 1)[1]

    before_p = client.get(f"/a/{agent_id}/ban-page")
    assert before_p.status_code == 200
    before_s = client.get(f"/?{stateless_query}")
    assert before_s.status_code == 200

    banned = client.post(
        "/admin/fragments/agents/toggle",
        data={
            "key": DEFAULT_SECRET,
            "agent_ref_id": str(agent_ref_id),
            "is_active": "0",
        },
    )
    assert banned.status_code == 200

    denied_token = client.get(
        "/api/agent/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert denied_token.status_code == 403
    after_p = client.get(f"/a/{agent_id}/ban-page")
    assert after_p.status_code == 404
    after_s = client.get(f"/?{stateless_query}")
    assert after_s.status_code == 403


def test_admin_users_create_fragment_validation_and_duplicate():
    no_key = client.post(
        "/admin/fragments/users/create",
        data={"key": "", "new_user_key": "mini-a", "new_user_comment": "x"},
    )
    assert no_key.status_code == 200
    assert "Нужен admin ключ" in no_key.text

    ok = client.post(
        "/admin/fragments/users/create",
        data={
            "key": DEFAULT_SECRET,
            "new_user_key": "mini-create-fragment",
            "new_user_comment": "note",
        },
    )
    assert ok.status_code == 200
    assert "Список пользователей" in ok.text

    duplicate = client.post(
        "/admin/fragments/users/create",
        data={
            "key": DEFAULT_SECRET,
            "new_user_key": "mini-create-fragment",
            "new_user_comment": "note",
        },
    )
    assert duplicate.status_code == 200
    assert "Ключ уже существует" in duplicate.text
