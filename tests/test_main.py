from fastapi.testclient import TestClient
from main import app, DEFAULT_SECRET

client = TestClient(app)


def test_admin_page():
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Генератор ссылок" in response.text


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


def test_admin_users_fragment_with_admin_key():
    response = client.get(f"/admin/fragments/users?key={DEFAULT_SECRET}")
    assert response.status_code == 200
    assert "Список пользователей" in response.text


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
