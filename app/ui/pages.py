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

  text.textContent = data.url;
  anchor.href = data.url;
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
    onKeyChange();
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
    loadApps();
  } else if (tabName === 'users') {
    document.getElementById('content-users').classList.remove('is-hidden');
    document.getElementById('tab-users').classList.add('is-active');
    loadUsers();
  }
}

async function onKeyChange() {
  const key = document.getElementById('key').value.trim();
  const usersTab = document.getElementById('tab-users');
  if (!key) {
    usersTab.classList.add('is-hidden');
    return;
  }
  try {
    const response = await fetch(`/api/users?key=${encodeURIComponent(key)}`);
    if (response.ok) {
      usersTab.classList.remove('is-hidden');
    } else {
      usersTab.classList.add('is-hidden');
      if (currentTab === 'users') switchTab('saved');
    }
  } catch {
    usersTab.classList.add('is-hidden');
  }
}

async function loadApps() {
  const key = document.getElementById('key').value.trim();
  const listDiv = document.getElementById('apps-list');
  if (!key) {
    listDiv.innerHTML = '<p class="has-text-grey-light is-italic">Введите ключ чтобы увидеть приложения...</p>';
    return;
  }
  try {
    const response = await fetch(`/api/apps?key=${encodeURIComponent(key)}`);
    if (!response.ok) {
      listDiv.innerHTML = '<p class="has-text-danger">Ошибка загрузки приложений</p>';
      return;
    }
    const apps = await response.json();
    if (!apps.length) {
      listDiv.innerHTML = '<p class="has-text-grey-light is-italic">Список пуст</p>';
      return;
    }
    listDiv.innerHTML = apps.map(a => {
      const href = a.user_id === 1 ? `/p/${a.slug}` : `/p${a.user_id}/${a.slug}`;
      return `<div class="box p-3 mb-3"><div class="is-flex is-justify-content-space-between is-align-items-center"><div><strong>${a.slug}</strong><div class="is-size-7 has-text-grey">${href}</div></div><a class="button is-small is-link is-light" href="${href}" target="_blank">Открыть</a></div></div>`;
    }).join('');
  } catch {
    listDiv.innerHTML = '<p class="has-text-danger">Ошибка загрузки приложений</p>';
  }
}

async function saveApp() {
  const key = document.getElementById('key').value.trim();
  const slug = document.getElementById('app-slug').value.trim();
  const html = document.getElementById('code').value;
  if (!key || !slug) {
    alert('Нужны ключ и имя ссылки');
    return;
  }
  const response = await fetch('/api/apps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, slug, html })
  });
  const data = await response.json();
  if (!response.ok) {
    alert(data.detail || 'Ошибка сохранения');
    return;
  }
  await loadApps();
}

function generateUUIDKey() {
  const value = `mini${crypto.randomUUID().replaceAll('-', '').slice(0, 28)}`;
  document.getElementById('new-user-key').value = value;
}

async function loadUsers() {
  const key = document.getElementById('key').value.trim();
  const listDiv = document.getElementById('users-list');
  if (!key) {
    listDiv.innerHTML = '<p class="has-text-grey-light">Введите admin ключ</p>';
    return;
  }
  try {
    const response = await fetch(`/api/users?key=${encodeURIComponent(key)}`);
    if (!response.ok) {
      listDiv.innerHTML = '<p class="has-text-danger">Нет доступа к списку пользователей</p>';
      return;
    }
    const users = await response.json();
    const rows = users.map(u => {
      const s = u.stats || {};
      return `<tr><td>${u.id}</td><td><code>${u.key}</code></td><td>${u.comment || ''}</td><td>${s.generated || 0}</td><td>${s.view_stateless || 0}</td><td>${s.apps_count || 0}</td><td>${s.view_persistent || 0}</td></tr>`;
    }).join('');
    listDiv.innerHTML = `<div class="table-container"><table class="table is-fullwidth is-striped is-hoverable"><thead><tr><th>ID</th><th>Key</th><th>Comment</th><th>Gen</th><th>View URL</th><th>Apps</th><th>View /p</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  } catch {
    listDiv.innerHTML = '<p class="has-text-danger">Ошибка загрузки пользователей</p>';
  }
}

async function createUser() {
  const adminKey = document.getElementById('key').value.trim();
  const key = document.getElementById('new-user-key').value.trim();
  const comment = document.getElementById('new-user-comment').value.trim();
  if (!adminKey || !key) {
    alert('Нужны admin key и новый ключ');
    return;
  }
  const response = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ admin_key: adminKey, key, comment })
  });
  const data = await response.json();
  if (!response.ok) {
    alert(data.detail || 'Ошибка создания пользователя');
    return;
  }
  document.getElementById('new-user-key').value = '';
  document.getElementById('new-user-comment').value = '';
  await loadUsers();
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
                                    oninput="onKeyChange()",
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
                                Div(
                                    Span(id="link-text", cls="is-size-7"),
                                    cls="result-box p-3",
                                ),
                                cls="control is-expanded",
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
                                NotStr(
                                    """<div class="tabs is-centered mt-4"><ul><li id="tab-saved" class="is-active"><a onclick="switchTab('saved')">Сохраненные (DB)</a></li><li id="tab-users" class="is-hidden"><a onclick="switchTab('users')">Пользователи</a></li></ul></div>"""
                                )
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
                                            onclick="saveApp()",
                                        ),
                                        cls="control",
                                    ),
                                    cls="field has-addons mt-4",
                                ),
                                P(
                                    NotStr(
                                        "Приложение будет доступно по адресу <code>/p{id}/{имя}</code>"
                                    ),
                                    id="editing-status",
                                    cls="help mb-5",
                                ),
                                Div(id="apps-list", cls="mt-4"),
                                id="content-saved",
                            ),
                            Div(
                                H1("Управление Пользователями", cls="title is-6 mt-4"),
                                Div(
                                    Div(
                                        Label("Новый Ключ", cls="label"),
                                        Div(
                                            Input(
                                                cls="input",
                                                type="text",
                                                id="new-user-key",
                                                placeholder="Введите ключ или нажмите генерацию",
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
                                            cls="control has-addons",
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
                                        cls="button is-primary is-fullwidth",
                                        onclick="createUser()",
                                    ),
                                    cls="box has-background-light",
                                ),
                                Div(id="users-list"),
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
