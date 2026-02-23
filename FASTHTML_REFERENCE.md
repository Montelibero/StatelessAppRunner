# FastHTML - Практический справочник

> Собрано на основе реального проекта + исследования документации. Всё проверено в бою.

## Установка и инициализация проекта

```bash
uv init --name myproject
uv add python-fasthtml
uv run python main.py          # запуск (сервер на localhost:5001)
```

`pyproject.toml` — минимальный:
```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["python-fasthtml>=0.12.0"]
```

---

## Минимальное приложение

```python
from fasthtml.common import *

app, rt = fast_app()

@rt("/")
def get():
    return Titled("My App", P("Hello"))

serve()  # uvicorn на 0.0.0.0:5001, live reload
```

- `from fasthtml.common import *` — **так задумано**, экспортирует все HTML-теги как Python-функции
- `fast_app()` возвращает `(app, rt)` — ASGI-приложение и декоратор роутов
- `serve()` — обёртка над uvicorn с hot reload

---

## Роуты

Имя функции определяет HTTP-метод:

```python
@rt("/")
def get():           # GET /
    return P("hello")

@rt("/submit")
def post(name: str): # POST /submit, поле name из формы
    return P(f"Hi {name}")

@rt("/item/{id}")
def get(id: int):    # GET /item/42, автокаст типов
    return P(f"Item #{id}")

@rt("/search")
def get(q: str = "", page: int = 0):  # GET /search?q=hello&page=2
    return P(f"Search: {q}")
```

**Два роута на один путь** (GET + POST) — просто две функции:
```python
@rt("/form")
def get():
    return Form(Input(name="x"), Button("Go"), method="post")

@rt("/form")
def post(x: str):
    return P(f"Got: {x}")
```

### Async роуты

```python
@rt("/data")
async def get():
    data = await some_async_call()
    return P(str(data))
```

### Доступ к сырому Request (Starlette)

```python
from starlette.requests import Request

@rt("/api")
async def post(request: Request):
    body = await request.json()
    # ...
```

> **ВАЖНО**: если принимаешь JSON, надо именно `Request` — FastHTML по умолчанию парсит form data.

---

## HTML-компоненты

Все стандартные теги — Python-функции. Вложенность естественная:

```python
Main(
    Header(H1("Title"), Nav(A("Home", href="/"))),
    Section(
        H2("Content"),
        P("Text with ", Strong("bold"), "."),
        Ul(Li("One"), Li("Two")),
    ),
    Footer(P("footer")),
    cls="container"
)
```

### Атрибуты

```python
Div("content", cls="card", id="main")     # class → cls
Input(type="text", name="email")
Label("Name", For="name")                  # for → For
A("Link", href="/page", target="_blank")
Button("Go", disabled=True)
Div(style="color: red; padding: 8px;")
Script(src="...", defer=True)
Script(src="...", async_=True)              # async → async_
```

### data-* атрибуты

```python
Div("card", data_idx="5", data_theme="dark")
# → <div data-idx="5" data-theme="dark">card</div>
```

### Переиспользуемые компоненты — обычные функции

```python
def card(title, *content):
    return Div(
        H3(title, cls="font-bold"),
        *content,
        cls="card bg-base-200 p-4"
    )

# Использование:
card("Hello", P("World"), P("!"))
```

### Title — задаёт <title> страницы

```python
@rt("/")
def get():
    return Title("My Page"), Main(H1("Content"))
    # Можно вернуть кортеж — Title + тело
```

### Titled — готовая обёртка с заголовком

```python
return Titled("Page Title", P("Content"))
# Рендерит <title> + <h1> + контент, обёрнутый в layout
```

---

## HTMX-интеграция

FastHTML включает HTMX по умолчанию. Все `hx-*` атрибуты → `hx_*` kwargs:

### Основные паттерны

```python
# Клик → POST → заменить содержимое
Button("Save",
    hx_post="/save",
    hx_target="#result",
    hx_swap="innerHTML"     # default
)

# Select → GET → обновить блок
Select(
    Option("A", value="a"), Option("B", value="b"),
    hx_get="/fields",
    hx_target="#form-fields",
    hx_swap="innerHTML"
)

# Input → GET с debounce
Input(
    name="search",
    hx_get="/search",
    hx_target="#results",
    hx_trigger="keyup changed delay:300ms"
)

# Включить значения элементов вне формы
Button("Decode",
    hx_post="/decode",
    hx_target="#output",
    hx_include="#my-textarea"   # включить значение элемента
)
```

### hx_swap варианты

| Значение | Действие |
|----------|----------|
| `innerHTML` | Заменить содержимое (default) |
| `outerHTML` | Заменить весь элемент |
| `beforeend` | Добавить после последнего child |
| `afterbegin` | Вставить перед первым child |
| `none` | Не менять DOM |

### Фрагменты vs полные страницы

**Ключевой момент**: FastHTML автоматически определяет HTMX-запросы по заголовку `HX-Request: true`.
- HTMX-запрос → возвращается только фрагмент HTML
- Обычный запрос → оборачивается в полную HTML-страницу

```python
@rt("/fields")
def get(operation: str = ""):
    # При HTMX-запросе вернёт только этот Div
    # При обычном — обернёт в <html><head>...</head><body>...</body></html>
    return Div(
        Label("Name"), Input(name="name"),
        cls="form-control"
    )
```

### Форма + HTMX (без перезагрузки)

```python
Form(
    Input(name="query"),
    Button("Search"),
    hx_post="/search",
    hx_target="#results",
    hx_swap="innerHTML"
)
```

> **ВАЖНО**: все input/select элементы должны быть **внутри** Form, чтобы их значения отправлялись. Если select вне формы — его значение не попадёт в POST.

### JS-вызов при HTMX из JavaScript

Если нужно сделать fetch как HTMX (получить фрагмент, а не полную страницу):

```javascript
fetch("/fields?operation=payment", {
    headers: { "HX-Request": "true" }
})
```

---

## Формы и POST

### Простой вариант — именованные параметры

```python
@rt("/submit")
def post(name: str, email: str = ""):
    # FastHTML автоматически извлекает поля формы по имени параметра
    return P(f"{name} <{email}>")
```

### Dataclass

```python
from dataclasses import dataclass

@dataclass
class Contact:
    name: str
    email: str

@rt("/submit")
def post(form: Contact):
    return P(f"{form.name} <{form.email}>")
```

### JSON body (не form data)

```python
from starlette.requests import Request

@rt("/api")
async def post(request: Request):
    body = await request.json()       # dict
    return PlainTextResponse("ok")
```

> **ВАЖНО**: для `PlainTextResponse` нужен импорт:
> `from starlette.responses import PlainTextResponse`

---

## Статические файлы

### Вариант 1: `static_path` в fast_app (работает с PicoCSS / default headers)

```python
app, rt = fast_app(static_path="static")
# Файлы из ./static/ доступны по /static/filename.ext
```

### Вариант 2: Явный mount через Starlette (надёжный, работает всегда)

```python
from starlette.staticfiles import StaticFiles

app, rt = fast_app(default_hdrs=False, ...)
app.mount("/static", StaticFiles(directory="static"), name="static")
```

> **GOTCHA**: при `default_hdrs=False` параметр `static_path` в `fast_app()` **НЕ РАБОТАЕТ**. Нужен явный `StaticFiles` mount. Это нас укусило.

### Структура

```
project/
├── main.py
└── static/
    ├── app.js
    └── style.css
```

В HTML:
```python
Script(src="/static/app.js", defer=True)
Link(href="/static/style.css", rel="stylesheet")
```

---

## Подключение внешних CSS-фреймворков (DaisyUI, Tailwind)

### Отключение PicoCSS (default стили FastHTML)

```python
app, rt = fast_app(
    pico=False,
    default_hdrs=False,     # убирает ВСЕ default заголовки (htmx, pico, etc.)
    hdrs=(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        # Свои стили/скрипты
        Link(href="https://cdn.jsdelivr.net/npm/daisyui@4.12.23/dist/full.min.css", rel="stylesheet"),
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/dist/htmx.min.js"),
        Script(src="/static/app.js", defer=True),
    ),
)
```

> **ВАЖНО**: при `default_hdrs=False` **HTMX не подключается автоматически** — его надо добавить вручную в `hdrs`.

### DaisyUI компоненты в FastHTML

```python
# Card
Div(
    H2("Title", cls="text-lg font-semibold"),
    P("Content"),
    cls="card bg-base-100 shadow p-6"
)

# Button
Button("Click", cls="btn btn-primary btn-sm")

# Input
Input(type="text", cls="input input-bordered w-full")

# Select
Select(
    Option("Choose...", disabled=True, selected=True),
    Option("A"), Option("B"),
    cls="select select-bordered select-sm w-full"
)

# Toast container
Div(id="toast-container", cls="toast toast-end toast-top z-50")
```

---

## CDN-библиотеки (JavaScript)

### Через hdrs в fast_app

```python
app, rt = fast_app(hdrs=(
    Script(src="https://cdn.jsdelivr.net/npm/@stellar/stellar-sdk@14.5.0/dist/stellar-sdk.js"),
    Script(src="/static/app.js", defer=True),
))
```

### Inline скрипт

```python
Script("""
    console.log("Inline JS");
    const sdk = StellarSdk;
""")
```

### ES Modules

```python
Script(
    src="https://cdn.jsdelivr.net/npm/some-lib/+esm",
    type="module"
)
```

---

## Паттерн: JSON API endpoint

Когда клиент отправляет JSON (не form data):

```python
from starlette.requests import Request
from starlette.responses import PlainTextResponse

@rt("/api/build")
async def post(request: Request):
    try:
        body = await request.json()
    except Exception:
        return PlainTextResponse("Invalid JSON", status_code=400)

    name = body.get("name", "")
    items = body.get("items", [])

    # ... обработка ...

    return PlainTextResponse("result text")
```

Клиентская сторона:
```javascript
fetch("/api/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "test", items: [1, 2, 3] })
})
.then(r => r.text())
.then(text => { /* ... */ });
```

---

## Паттерн: динамические формы (операции/шаги)

Задача: пользователь выбирает тип → появляются соответствующие поля.

### Сервер — описание полей как данные

```python
# Поля: (name, label, placeholder, default)
OP_FIELDS = {
    "payment": [
        ("destination", "Destination", "G...", ""),
        ("amount", "Amount", "100", ""),
    ],
    "transfer": [
        ("from_account", "From", "G...", ""),
        ("to_account", "To", "G...", ""),
        ("amount", "Amount", "0", ""),
    ],
}

@rt("/fields")
def get(operation: str = ""):
    fields = OP_FIELDS.get(operation)
    if not fields:
        return P("Select operation type")
    items = []
    for name, label, placeholder, default in fields:
        items.append(Div(
            Label(label, cls="label"),
            Input(type="text", name=name, placeholder=placeholder, value=default,
                  cls="input input-bordered input-sm w-full"),
            cls="form-control",
        ))
    return Div(*items, cls="grid grid-cols-2 gap-2")
```

### Клиент — запрос полей при смене select

```javascript
function onTypeChange(select) {
    fetch(`/fields?operation=${select.value}`, {
        headers: { "HX-Request": "true" }
    })
    .then(r => r.text())
    .then(html => {
        document.querySelector(".fields-container").innerHTML = html;
    });
}
```

Или чисто через HTMX-атрибуты:
```python
Select(
    Option("Payment", value="payment"),
    Option("Transfer", value="transfer"),
    hx_get="/fields",
    hx_target="#fields-container",
    hx_swap="innerHTML",
)
```

---

## Паттерн: множественные блоки (add/remove)

Задача: пользователь добавляет N карточек (операций, полей, элементов).

**Подход**: управление на клиенте (JS), сбор данных и отправка JSON на сервер.

```javascript
let counter = 1;

function addCard() {
    const list = document.getElementById("cards-list");
    const card = document.createElement("div");
    card.className = "card bg-base-200 p-4";
    card.innerHTML = `
        <div class="flex justify-between">
            <span class="font-semibold">Item #${counter + 1}</span>
            <button onclick="this.closest('.card').remove()">✕</button>
        </div>
        <select onchange="loadFields(this)">
            <option value="">Choose...</option>
            <option value="type_a">Type A</option>
        </select>
        <div class="fields"></div>
    `;
    list.appendChild(card);
    counter++;
}

function collectAll() {
    const cards = document.querySelectorAll("#cards-list .card");
    const items = [];
    for (const card of cards) {
        const data = {};
        card.querySelectorAll("input, select").forEach(el => {
            if (el.name) data[el.name] = el.value;
        });
        items.push(data);
    }
    return items;
}
```

---

## Собранные gotchas и подводные камни

| Проблема | Причина | Решение |
|----------|---------|---------|
| `static/app.js` отдаёт 404 | `default_hdrs=False` ломает `static_path` | Явный `app.mount("/static", StaticFiles(...))` |
| `PlainTextResponse is not defined` | Не импортирован из starlette | `from starlette.responses import PlainTextResponse` |
| Select вне Form — значение не отправляется | HTMX/HTML отправляет только поля внутри формы | Переместить select внутрь Form |
| HTMX-запрос возвращает полную страницу | Нет заголовка `HX-Request` | Добавить `headers: {"HX-Request": "true"}` в fetch |
| HTMX не работает после `default_hdrs=False` | HTMX не подключен | Добавить Script с HTMX CDN в `hdrs` |
| `pico=True` конфликтует с Tailwind/DaisyUI | Два CSS-фреймворка | `pico=False, default_hdrs=False` |
| `Request` не определён | Не импортирован | `from starlette.requests import Request` |

---

## Полезные импорты (шпаргалка)

```python
from fasthtml.common import *                        # Все HTML-теги + fast_app, serve, etc.
from starlette.requests import Request               # Доступ к сырому запросу (JSON body, headers)
from starlette.responses import PlainTextResponse     # Текстовый ответ (не HTML)
from starlette.responses import JSONResponse          # JSON ответ
from starlette.responses import RedirectResponse      # Редирект
from starlette.staticfiles import StaticFiles         # Раздача статики
```

---

## Шаблон нового проекта (DaisyUI + HTMX)

```python
from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles

app, rt = fast_app(
    pico=False,
    default_hdrs=False,
    hdrs=(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Title("My App"),
        Link(href="https://cdn.jsdelivr.net/npm/daisyui@4.12.23/dist/full.min.css", rel="stylesheet"),
        Script(src="https://cdn.tailwindcss.com"),
        Script(src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.7/dist/htmx.min.js"),
        Script(src="/static/app.js", defer=True),
    ),
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@rt("/")
def get():
    return Div(
        Div(
            A("My App", cls="text-xl font-bold", href="/"),
            cls="navbar bg-base-300 rounded-box mb-6",
        ),
        Div(
            H2("Hello", cls="text-lg font-semibold"),
            P("Your content here"),
            cls="card bg-base-100 shadow p-6",
        ),
        Div(id="toast-container", cls="toast toast-end toast-top z-50"),
        cls="container mx-auto max-w-3xl p-4",
    )

serve()
```

```bash
mkdir -p static && touch static/app.js
uv run python main.py
```
