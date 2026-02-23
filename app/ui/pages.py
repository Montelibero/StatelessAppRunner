from fasthtml.common import (
    A,
    Body,
    Button,
    Div,
    Head,
    H1,
    Html,
    I,
    Input,
    Label,
    Li,
    Link,
    Meta,
    NotStr,
    P,
    Script,
    Section,
    Span,
    Style,
    Textarea,
    Title,
    Ul,
    to_xml,
)


HOME_STYLE = """
.hero-body { display: flex; justify-content: center; align-items: center; }
.box { max-width: 600px; width: 100%; border-top: 4px solid var(--bulma-link); }
.footer-link { display: inline-flex; align-items: center; gap: 6px; color: var(--bulma-text); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: var(--bulma-link); }
"""


ADMIN_STYLE = """
.textarea-code { font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace; min-height: 250px; }
.result-box { border: 1px solid var(--bulma-border); word-break: break-all; max-height: 200px; overflow-y: auto; font-family: monospace; }
.admin-tabs .tabs { margin-bottom: 0.75rem; }
.admin-tabs .tabs li a { font-weight: 600; }
.limit-progress-wrapper { width: 120px; height: 6px; background-color: var(--bulma-background-weak); border-radius: 99px; overflow: hidden; }
.limit-progress-bar { height: 100%; background-color: var(--bulma-link); width: 0%; transition: width 0.3s, background-color 0.3s; }
"""


ADMIN_SCRIPT = """
function toggleKeyVisibility() {
  const input = document.getElementById('key');
  const icon = document.getElementById('eye-icon');
  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.replace('ph-eye', 'ph-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.replace('ph-eye-slash', 'ph-eye');
  }
}

async function generate() {
  const key = document.getElementById('key').value.trim();
  const html = document.getElementById('code').value;
  const compress = document.getElementById('compress').checked;

  if (!key) {
    alert('Введите секретный ключ');
    return;
  }

  const resp = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, html, compress, domain: '' })
  });

  const data = await resp.json();
  if (!resp.ok) {
    alert(data.detail || 'Ошибка генерации');
    return;
  }

  const result = document.getElementById('result');
  const text = document.getElementById('link-text');
  const anchor = document.getElementById('link-anchor');
  const lenInfo = document.getElementById('len-info');
  const limitBar = document.getElementById('limit-bar');
  const limitWarn = document.getElementById('limit-warning');
  const hardLimit = 8193;
  const tgRecommendedLimit = 4096;
  const urlLength = data.url.length;
  const percentage = Math.min((urlLength / hardLimit) * 100, 100);

  text.textContent = data.url;
  anchor.href = data.url;
  lenInfo.textContent = String(urlLength);
  limitBar.style.width = `${percentage}%`;

  if (percentage > 90) {
    limitBar.style.backgroundColor = 'var(--bulma-danger)';
  } else if (percentage > 70) {
    limitBar.style.backgroundColor = 'var(--bulma-warning)';
  } else {
    limitBar.style.backgroundColor = 'var(--bulma-link)';
  }

  if (urlLength > tgRecommendedLimit) {
    limitWarn.classList.remove('is-hidden');
  } else {
    limitWarn.classList.add('is-hidden');
  }

  result.classList.remove('is-hidden');
}

function copyLink() {
  const text = document.getElementById('link-text').textContent || '';
  if (!text) return;
  navigator.clipboard.writeText(text);
}

let currentTab = 'saved';

function toggleAdvancedPanel() {
  const panel = document.getElementById('advanced-panel');
  panel.classList.toggle('is-hidden');
  if (!panel.classList.contains('is-hidden')) {
    switchTab(currentTab);
  }
}

function switchTab(tabName) {
  currentTab = tabName;
  document.getElementById('content-saved').classList.add('is-hidden');
  document.getElementById('content-users').classList.add('is-hidden');
  document.getElementById('tab-saved').classList.remove('is-active');
  document.getElementById('tab-users').classList.remove('is-active');

  if (tabName === 'saved') {
    document.getElementById('content-saved').classList.remove('is-hidden');
    document.getElementById('tab-saved').classList.add('is-active');
    document.getElementById('refresh-apps-btn').click();
  } else if (tabName === 'users') {
    document.getElementById('content-users').classList.remove('is-hidden');
    document.getElementById('tab-users').classList.add('is-active');
    document.getElementById('refresh-users-btn').click();
  }
}

function generateUUIDKey() {
  const value = `mini${crypto.randomUUID().replaceAll('-', '').slice(0, 28)}`;
  document.getElementById('new-user-key').value = value;
}
"""


def _document(title: str, body_children: list) -> str:
    return to_xml(
        Html(
            Head(
                Meta(charset="UTF-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title(title),
                Link(
                    rel="stylesheet",
                    href="https://cdn.jsdelivr.net/npm/bulma@1.0.0/css/bulma.min.css",
                ),
                Script(src="https://unpkg.com/htmx.org@1.9.12"),
                Script(src="https://unpkg.com/@phosphor-icons/web"),
            ),
            Body(*body_children),
            lang="ru",
        )
    )


def render_home_page() -> str:
    return _document(
        "Stateless App Runner",
        [
            Style(HOME_STYLE),
            Section(
                Div(
                    Div(
                        Div(
                            Span(
                                I(
                                    cls="ph ph-rocket-launch",
                                    style="font-size: 48px;",
                                ),
                                cls="icon is-large has-text-link mb-4",
                            ),
                            H1("Stateless App Runner", cls="title is-3 mb-3"),
                            P(
                                NotStr(
                                    "Безопасная среда для запуска HTML/JS приложений. <br>"
                                    "Весь код содержится внутри ссылки."
                                ),
                                cls="subtitle is-6 has-text-grey",
                            ),
                            Div(
                                A(
                                    Span(
                                        I(cls="ph ph-magic-wand"),
                                        cls="icon",
                                    ),
                                    Span("Перейти в Генератор"),
                                    href="/admin",
                                    cls="button is-link is-medium is-rounded",
                                ),
                                cls="buttons is-centered mt-5",
                            ),
                            cls="box p-6 mx-auto",
                        ),
                        Div(
                            A(
                                I(cls="ph ph-github-logo is-size-4"),
                                Span(
                                    "View source on GitHub",
                                    cls="has-text-weight-medium",
                                ),
                                href="https://github.com/Montelibero/StatelessAppRunner",
                                target="_blank",
                                cls="footer-link",
                            ),
                            cls="mt-6",
                        ),
                        cls="container has-text-centered",
                    ),
                    cls="hero-body",
                ),
                cls="hero is-fullheight is-light",
            ),
        ],
    )


def _app_href(app_item: dict) -> str:
    user_id = app_item.get("user_id", 1)
    slug = app_item["slug"]
    if user_id == 1:
        return f"/p/{slug}"
    return f"/p{user_id}/{slug}"


def render_apps_fragment(
    apps: list[dict] | None = None, *, info: str | None = None, error: str | None = None
) -> str:
    if error:
        return to_xml(P(error, cls="has-text-danger"))
    if info:
        return to_xml(P(info, cls="has-text-grey-light is-italic"))
    if not apps:
        return to_xml(P("Список пуст", cls="has-text-grey-light is-italic"))

    cards = []
    for app_item in apps:
        href = _app_href(app_item)
        cards.append(
            Div(
                Div(
                    Span(app_item["slug"], cls="has-text-weight-semibold"),
                    P(href, cls="is-size-7 has-text-grey"),
                    Span(
                        f"{app_item.get('html_bytes', 0)} B",
                        cls="tag is-light is-size-7",
                    ),
                    cls="is-flex-grow-1",
                ),
                A(
                    "Открыть",
                    href=href,
                    target="_blank",
                    cls="button is-small is-link is-light",
                ),
                cls="box p-3 mb-3 is-flex is-justify-content-space-between is-align-items-center",
                style="gap: 8px;",
            )
        )
    return to_xml(Div(*cards))


def render_users_fragment(
    users: list[dict] | None = None,
    *,
    info: str | None = None,
    error: str | None = None,
) -> str:
    if error:
        return to_xml(P(error, cls="has-text-danger"))
    if info:
        return to_xml(P(info, cls="has-text-grey-light is-italic"))
    if not users:
        return to_xml(
            P("Список пользователей пуст", cls="has-text-grey-light is-italic")
        )

    cards = [P("Список пользователей", cls="has-text-weight-semibold mb-3")]
    for user in users:
        stats = user.get("stats", {})
        cards.append(
            Div(
                Div(
                    Span(f"ID {user['id']}", cls="tag is-light"),
                    Span(user["key"], cls="ml-2 is-family-monospace"),
                    cls="mb-2",
                ),
                P(user.get("comment") or "", cls="is-size-7 has-text-grey mb-2"),
                Div(
                    Span(
                        f"Gen {stats.get('generated', 0)}", cls="tag is-info is-light"
                    ),
                    Span(
                        f"View URL {stats.get('view_stateless', 0)}",
                        cls="tag is-link is-light ml-1",
                    ),
                    Span(
                        f"Apps {stats.get('apps_count', 0)}",
                        cls="tag is-success is-light ml-1",
                    ),
                    Span(
                        f"View /p {stats.get('view_persistent', 0)}",
                        cls="tag is-warning is-light ml-1",
                    ),
                ),
                cls="box p-3 mb-3",
            )
        )
    return to_xml(Div(*cards))


def render_admin_page() -> str:
    return _document(
        "Link Generator Pro",
        [
            Style(ADMIN_STYLE),
            Section(
                Div(
                    Div(
                        Div(
                            Span(
                                I(cls="ph ph-link", style="font-size: 32px;"),
                                cls="icon is-large has-text-link",
                            ),
                            H1("Генератор ссылок", cls="title is-4 mb-0"),
                            cls="is-flex is-align-items-center mb-5",
                            style="gap: 10px;",
                        ),
                        Div(
                            Label("Секретный ключ", cls="label"),
                            Div(
                                Input(
                                    type="password",
                                    id="key",
                                    placeholder="Введите ваш секретный ключ",
                                    cls="input is-medium",
                                ),
                                Span(
                                    I(cls="ph ph-eye", id="eye-icon"),
                                    cls="icon is-right",
                                    onclick="toggleKeyVisibility()",
                                    style="cursor: pointer;",
                                ),
                                cls="control has-icons-right",
                            ),
                            cls="field",
                        ),
                        Div(
                            Div(
                                Label("HTML Код приложения", cls="label"),
                                Label(
                                    Input(type="checkbox", id="compress"),
                                    Span(" Сжимать (Gzip)", cls="is-size-7"),
                                ),
                                cls="is-flex is-justify-content-space-between is-align-items-center",
                            ),
                            Textarea(
                                cls="textarea textarea-code",
                                id="code",
                                placeholder="<!DOCTYPE html>...",
                            ),
                            cls="field",
                        ),
                        Div(
                            Button(
                                Span(I(cls="ph ph-magic-wand"), cls="icon"),
                                Span("Сгенерировать ссылку"),
                                id="generate-btn",
                                cls="button is-link is-fullwidth is-medium",
                                onclick="generate()",
                            ),
                            cls="field mt-5",
                        ),
                        Div(
                            Div(
                                P(
                                    "Готово",
                                    cls="has-text-weight-semibold has-text-link mb-0",
                                ),
                                Div(
                                    Span(
                                        Span("0", id="len-info"),
                                        " / 8193 байт",
                                        cls="is-size-7 mr-2",
                                    ),
                                    Div(
                                        Div(id="limit-bar", cls="limit-progress-bar"),
                                        cls="limit-progress-wrapper",
                                    ),
                                    cls="is-flex is-align-items-center",
                                ),
                                cls="is-flex is-justify-content-space-between is-align-items-center mb-3",
                            ),
                            Div(
                                Span(id="link-text", cls="is-size-7"),
                                cls="result-box p-3",
                            ),
                            P(
                                "В Telegram длинные URL могут открываться нестабильно, лучше держать длину до ~4096 байт.",
                                id="limit-warning",
                                cls="help is-danger mt-2 is-hidden",
                            ),
                            Div(
                                A(
                                    Span(I(cls="ph ph-arrow-square-out"), cls="icon"),
                                    Span("Открыть"),
                                    id="link-anchor",
                                    href="#",
                                    target="_blank",
                                    cls="button is-small is-outlined is-link",
                                ),
                                Button(
                                    Span(I(cls="ph ph-copy"), cls="icon"),
                                    Span("Копировать"),
                                    cls="button is-small is-link",
                                    onclick="copyLink()",
                                ),
                                cls="buttons is-right mt-3",
                            ),
                            id="result",
                            cls="box mt-5 is-hidden",
                        ),
                        Div(
                            Button(
                                Span(I(cls="ph ph-gear"), cls="icon"),
                                Span("Расширенная админка"),
                                id="advanced-btn",
                                cls="button is-light is-fullwidth mt-4",
                                onclick="toggleAdvancedPanel()",
                            ),
                        ),
                        Div(
                            Div(
                                Div(
                                    Ul(
                                        Li(
                                            A(
                                                "Сохраненные (DB)",
                                                onclick="switchTab('saved')",
                                            ),
                                            id="tab-saved",
                                            cls="is-active",
                                        ),
                                        Li(
                                            A(
                                                "Пользователи",
                                                onclick="switchTab('users')",
                                            ),
                                            id="tab-users",
                                        ),
                                    ),
                                    cls="tabs is-boxed is-fullwidth",
                                ),
                                cls="admin-tabs mt-4",
                            ),
                            Div(
                                Div(
                                    Div(
                                        Input(
                                            cls="input",
                                            type="text",
                                            id="app-slug",
                                            placeholder="Имя ссылки (например, my-app)",
                                        ),
                                        cls="control is-expanded",
                                    ),
                                    Div(
                                        Button(
                                            Span(
                                                I(cls="ph ph-floppy-disk"), cls="icon"
                                            ),
                                            Span("Сохранить"),
                                            id="save-btn",
                                            cls="button is-primary",
                                            hx_post="/admin/fragments/apps/save",
                                            hx_include="#key,#app-slug,#code",
                                            hx_target="#apps-list",
                                            hx_swap="innerHTML",
                                        ),
                                        cls="control",
                                    ),
                                    cls="field has-addons mt-4",
                                ),
                                P(
                                    "Приложение будет доступно по адресу /p{id}/{имя}",
                                    id="editing-status",
                                    cls="help mb-4",
                                ),
                                Button(
                                    "Обновить список",
                                    id="refresh-apps-btn",
                                    cls="button is-small is-light",
                                    hx_get="/admin/fragments/apps",
                                    hx_include="#key",
                                    hx_target="#apps-list",
                                    hx_swap="innerHTML",
                                ),
                                Div(
                                    "Введите ключ чтобы увидеть приложения...",
                                    id="apps-list",
                                    cls="mt-4 has-text-grey-light is-italic",
                                ),
                                id="content-saved",
                            ),
                            Div(
                                H1("Управление Пользователями", cls="title is-6 mt-4"),
                                Div(
                                    Div(
                                        Label("Новый Ключ", cls="label"),
                                        Div(
                                            Div(
                                                Input(
                                                    cls="input",
                                                    type="text",
                                                    id="new-user-key",
                                                    placeholder="Введите ключ или нажмите генерацию",
                                                ),
                                                cls="control is-expanded",
                                            ),
                                            Div(
                                                Button(
                                                    Span(
                                                        I(cls="ph ph-arrows-clockwise"),
                                                        cls="icon",
                                                    ),
                                                    cls="button is-info",
                                                    onclick="generateUUIDKey()",
                                                ),
                                                cls="control",
                                            ),
                                            cls="field has-addons",
                                        ),
                                        cls="field",
                                    ),
                                    Div(
                                        Label("Комментарий", cls="label"),
                                        Div(
                                            Input(
                                                cls="input",
                                                type="text",
                                                id="new-user-comment",
                                                placeholder="Имя пользователя или описание",
                                            ),
                                            cls="control",
                                        ),
                                        cls="field",
                                    ),
                                    Button(
                                        "Создать пользователя",
                                        id="create-user-btn",
                                        cls="button is-primary is-fullwidth",
                                        hx_post="/admin/fragments/users/create",
                                        hx_include="#key,#new-user-key,#new-user-comment",
                                        hx_target="#users-list",
                                        hx_swap="innerHTML",
                                    ),
                                    Button(
                                        "Обновить пользователей",
                                        id="refresh-users-btn",
                                        cls="button is-light is-fullwidth mt-2",
                                        hx_get="/admin/fragments/users",
                                        hx_include="#key",
                                        hx_target="#users-list",
                                        hx_swap="innerHTML",
                                    ),
                                    cls="box has-background-light",
                                ),
                                Div(
                                    "Введите admin ключ для списка пользователей",
                                    id="users-list",
                                    cls="has-text-grey-light is-italic",
                                ),
                                id="content-users",
                                cls="is-hidden",
                            ),
                            id="advanced-panel",
                            cls="is-hidden",
                        ),
                        cls="box",
                    ),
                    cls="container is-max-desktop",
                ),
                cls="section",
            ),
            Script(ADMIN_SCRIPT),
        ],
    )
