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
    gen_response = client.post("/api/generate", json={
        "domain": "",
        "key": DEFAULT_SECRET,
        "html": html_source
    })
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
