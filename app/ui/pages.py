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
                        cls="box",
                    ),
                    cls="container is-max-desktop",
                ),
                cls="section",
            ),
            Script(ADMIN_SCRIPT),
        ],
    )
