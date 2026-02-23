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
.home-box { max-width: 920px; width: 100%; border-top: 4px solid var(--bulma-link); }
.skill-line { font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace; background: var(--bulma-scheme-main-bis); border: 1px solid var(--bulma-border); border-radius: 6px; padding: 12px; word-break: break-word; }
.example-box { background: var(--bulma-scheme-main-bis); border: 1px solid var(--bulma-border); border-radius: 8px; padding: 12px; }
.footer-link { display: inline-flex; align-items: center; gap: 6px; color: var(--bulma-text); text-decoration: none; transition: color 0.2s; }
.footer-link:hover { color: var(--bulma-link); }
.cta-row { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
.grid-2 { display: grid; gap: 12px; grid-template-columns: 1fr; }
@media (min-width: 769px) { .grid-2 { grid-template-columns: 1fr 1fr; } }
.panel-card { border: 1px solid var(--bulma-border); border-radius: 10px; background: var(--bulma-scheme-main-bis); padding: 14px; text-align: left; }
.mini-note { font-size: 0.85rem; color: var(--bulma-text-weak); }
"""


HOME_EXAMPLE_STATELESS_URL = "https://mtlminiapps.us/?d=eNq1GEuP2kb4zq-YddUAuxjMa7PLwh6yyUqRmrTKJqqiNJUGewzTNR40HsOSh5T00kMqVeolUk89Vb01irLabaq0h_wB84_6jW3AL2BpVBDGM9_7OZ_d3rr55dH9h1_dQn0xsA5zbfmHLGz3Ogp3FblBsHGYQ_BpD4jASO9j7hDRUR7cP1b3lCjIxgPSUUaUjIeMCwXpzBbEBtQxNUS_Y5AR1YnqL0qI2lRQbKmOji3SqZa1GStBhUUOb2J-iu4wg6AjbOmuhQXj7UoAC_AcMZndy0-XGRP0dL6UnwHmPWq3kHYQ2x5iw6B2L7XfJ7TXFy1U1bRRPw4yqDO08KSFTIucxUHfuY6g5kQNjW0hHa6Ex5GwRXu2SgUZONkIXayf9jhzbQMYWYy30GdVIr9xNBOEqCYeUAt0UfFwaBHVmTjAt4RuWNQ-vYP1E399DJglpJyQHiPowW2lhO6xLhOshBxsO6pDODXjvNmIcNNi4xbqU8Mg9gL6PDe_LevzaCScnWFBzZDfJc6vacOEJ7uMG4SrHBvUdbIRzlSnjw2po-bDUVNeeK-LC1rJ_5abxTiRn24tVI-zi5oUBne9PZqWyJgZoIENsqcdoMo28v6YvvDee5fen8i78M69v-D3YfoKltuV5aHMHzGXU8LRXTLOl9CA2cwZYj0r-g59QsA55SYngzhYkDOh-pnWQlym8n_1fLWWRAgqSYUEEmyQxWGWPOpZC2FXsCXQSTq5_Bj1oTRU3-IWstmY42F2ae6mBK-ozLVFlypdyUMltpGZJxDcE50zy-pijmTzAWdCSPhMhWiAZznVaqlj0j2lELY56dO5NQ0wBiRcgUgVfXfQBdJFVkLa1ev1g1TVBDwXTLsuxAwqvsepkUjxue8kLO4auaOC5wAOkYE8dwc2cOdkSLAoNEqoavJiBomMvcrZGHB3m8lY9fAwmVwRTQNFk1XoWyeTwiarc7aRlBaplmpGtfjgcRiJZqqyXe7I0h4yms6bWdmbprm2i9eJ_CYKlUMLhtOPQaFiy0JaueogrAs6SiC60KahVVtEF1ku-P9PpVjDBQ_DNdZsa8UVoWwFJiUi6hsPZQNtxL-VCfawALyLy2XHTU8L6ssGk5BjUkvIzOn6rdAmjlOolqvFZaXt_ea99c6n33t_e2-hXZ-j6UtYXEL_vowVdlfYKidGrBTnwSZmAz6xmpb4DOzskWwSc_96vbobJYnT9jghUBRo7Vlb05tNcoDSJcmlB6G32qgenFA_T19NX4Kd7703058Q_H2AxT9y2UJg8zncn09fTH9Edd8JcJ5J3MvkARYZlz6PyI31HjDgCeEsERpfraCnhJrVAs1-9y5DaUnNosIDV7Ur4QDYrgQjaltOgIe5XNugI6Rb2HE6ymJamU2XEWBYPgqixmJxqLUrgJPGjvZRZTF2trdUFUarMaoiVY1sh91sRhxkjYKYrVtUPwXNLIL5zUBooagcHrUrAclKHkEmRdjACAjnVSFfyQOPjxefxmTbZ_L605iokom64JH2VC3TUylG1yWj68uVSRHsSYK9DQj2JcH-p5m7I3nsrDK3fjVzG5JRYwPtm5KguQHBriTYTRPEVfZ-iVSd96v3BvoibCC4vJn-AB0R_mWjlOPtO7h5CY0CmgMA3gXbEv3Su_AJki1kTYn4zS5aJGH5ElkhnVVOblzNyVXpguoGPqtJgtoGBHVJUF_nZKlyc503ZOfMyDhNStA2UKksCcpxgrDJhX-5NkyadCgCGMwMjphPtR1kMN0dwHRQ7hFxyyLy9sbkNjAOUfLhoWoRgcjZkMNRC6MNEObzCwB17hHHtQRsm9hy5Enlw0zX1uUkhEJt5euFYuS8oCYqzGmvXUNbj6DkSgjaDFy25aWSf1ymYLNrECcgLybOm0ylEkMUsLAJvw-PUBJHSyCltF8cRojAOqZmUvwK4lzMzgxVOr4y6NkztAR4i3PG8ymRwE26Am1JnHIKvtTwhN3Pc-m7-Y0M64g6LraOpKiO_2roIJfSwdcTzpY4cv7j6_wy5Eoa-SKCnFtuwk4nQrigiGTATlLPFLfgqesLYkqPxDe_li8TAtLnifyNH-gRf69NsKXpmZ04KcGLJhmRKvgkIye2FrKK8DAnXJ54Ek9RVB59q6n7O9-o25Xy40pZEEcUIkyyEkv0YeRENhkjPzkLym17BI8aRvDqUCkmUyy2lEnFZ1YToItKS4y3afOocyzfK5ICDysRCoc6d_Hd2cYm-qY1XSp8rvFQvhw9thg8JAd7ZcGO6RkxCnvF4gpXZyVJwOBgeSubSzgRnNq9QnFp0xLcjfUsHQu9jwqkmP1GIJ6rQYs5uHpLXS44TGCY3cPzBm6DsR2mePkC-l__0HOU&s=4f6cc4a5c46a27d47b4ee983870fe417da42660cdeb799f28a3cb663dc1f08d5"


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
  const hardLimit = 8193;
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
  document.getElementById('content-agents').classList.add('is-hidden');
  document.getElementById('tab-saved').classList.remove('is-active');
  document.getElementById('tab-users').classList.remove('is-active');
  document.getElementById('tab-agents').classList.remove('is-active');

  if (tabName === 'saved') {
    document.getElementById('content-saved').classList.remove('is-hidden');
    document.getElementById('tab-saved').classList.add('is-active');
    document.getElementById('refresh-apps-btn').click();
  } else if (tabName === 'users') {
    document.getElementById('content-users').classList.remove('is-hidden');
    document.getElementById('tab-users').classList.add('is-active');
    document.getElementById('refresh-users-btn').click();
  } else if (tabName === 'agents') {
    document.getElementById('content-agents').classList.remove('is-hidden');
    document.getElementById('tab-agents').classList.add('is-active');
    document.getElementById('refresh-agents-btn').click();
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
                            P(
                                "the front page of the agent internet",
                                cls="is-size-7 has-text-grey mb-2",
                            ),
                            H1("Stateless App Runner", cls="title is-3 mb-2"),
                            P(
                                "Publish agent-created mini-apps as a signed link (HTML/JS in URL).",
                                cls="subtitle is-6 has-text-grey",
                            ),
                            P(
                                "Signed URL pages for AI agents (stateless by default).",
                                cls="mini-note mb-4",
                            ),
                            Div(
                                A(
                                    "Agent Quickstart",
                                    href="#agent-quickstart",
                                    cls="button is-link",
                                ),
                                A(
                                    "Docs for LLMs (llm.txt / skill.md)",
                                    href="#llm",
                                    cls="button is-light",
                                ),
                                A(
                                    "Open working example",
                                    href=HOME_EXAMPLE_STATELESS_URL,
                                    target="_blank",
                                    cls="button is-info is-light",
                                ),
                                cls="cta-row mb-5",
                            ),
                            Div(
                                P("What you can publish", cls="title is-5 mb-3"),
                                Div(
                                    Div(
                                        P(
                                            "Info page",
                                            cls="has-text-weight-semibold mb-1",
                                        ),
                                        P(
                                            "One-page reports, status pages, and compact dashboards.",
                                            cls="is-size-7",
                                        ),
                                        cls="panel-card",
                                    ),
                                    Div(
                                        P(
                                            "Interactive mini-app",
                                            cls="has-text-weight-semibold mb-1",
                                        ),
                                        P(
                                            "Small forms, calculators, and interactive browser UIs.",
                                            cls="is-size-7",
                                        ),
                                        cls="panel-card",
                                    ),
                                    cls="grid-2 mb-4",
                                ),
                                P("How it works", cls="title is-5 mb-3"),
                                Div(
                                    P(
                                        "1. Register and get Bearer token.",
                                        cls="is-size-7 mb-1",
                                    ),
                                    P(
                                        "2. POST /api/agent/generate and receive signed URL.",
                                        cls="is-size-7 mb-1",
                                    ),
                                    P(
                                        "3. Open link in browser: page payload is in URL, code runs client-side.",
                                        cls="is-size-7 mb-1",
                                    ),
                                    P(
                                        "Default mode is stateless URL delivery; payload is encoded directly inside the link.",
                                        cls="is-size-7 mb-1",
                                    ),
                                    P(
                                        "Stateless links are signed to prevent tampering; code runs in the user's browser.",
                                        cls="is-size-7",
                                    ),
                                    cls="panel-card mb-4",
                                ),
                                Div(
                                    P(
                                        "Open working example",
                                        cls="has-text-weight-semibold mb-1",
                                    ),
                                    P(
                                        "Opens a page generated from an embedded payload.",
                                        cls="is-size-7 mb-2",
                                    ),
                                    A(
                                        "Open example",
                                        href=HOME_EXAMPLE_STATELESS_URL,
                                        target="_blank",
                                        cls="button is-small is-link is-light",
                                    ),
                                    cls="example-box mb-4",
                                ),
                                Div(
                                    P(
                                        "Agent Quickstart (copy-paste)",
                                        cls="title is-5 mb-3",
                                    ),
                                    Div(
                                        P(
                                            "1. Register and get token",
                                            cls="has-text-weight-semibold mb-1",
                                        ),
                                        P(
                                            "Run one script and copy bearer_token.",
                                            cls="is-size-7 mb-1",
                                        ),
                                        P(
                                            NotStr(
                                                '<a href="https://mtlminiapps.us/scripts/register_agent.py">https://mtlminiapps.us/scripts/register_agent.py</a> or <a href="https://mtlminiapps.us/scripts/register_agent.mjs">https://mtlminiapps.us/scripts/register_agent.mjs</a>'
                                            ),
                                            cls="skill-line mb-3",
                                        ),
                                        P(
                                            "2. Generate a stateless page",
                                            cls="has-text-weight-semibold mb-1",
                                        ),
                                        P(
                                            "POST https://mtlminiapps.us/api/agent/generate with Authorization: Bearer <token>",
                                            cls="skill-line mb-2",
                                        ),
                                        P(
                                            "compress default: true",
                                            cls="is-size-7 mb-1",
                                        ),
                                        P(
                                            "raw HTML limit: 100KB",
                                            cls="is-size-7 mb-3",
                                        ),
                                        P(
                                            "3. Optional persistent pages",
                                            cls="has-text-weight-semibold mb-1",
                                        ),
                                        P(
                                            "/a/{agent_id}/{slug} and retention is 7 days since last open (AGENT_APP_TTL_DAYS).",
                                            cls="is-size-7",
                                        ),
                                        id="agent-quickstart",
                                        cls="panel-card mb-4",
                                    ),
                                ),
                                Div(
                                    P(
                                        "Limits & retention",
                                        cls="has-text-weight-semibold mb-1",
                                    ),
                                    P(
                                        "Raw HTML <= 100KB; compress default true; persistent TTL 7 days since last open.",
                                        cls="is-size-7",
                                    ),
                                    cls="panel-card mb-4",
                                ),
                                Div(
                                    P("Docs for agents / LLMs", cls="title is-5 mb-2"),
                                    P(
                                        NotStr(
                                            'Canonical docs: <a href="https://mtlminiapps.us/skill.md">https://mtlminiapps.us/skill.md</a> and <a href="https://mtlminiapps.us/llm.txt">https://mtlminiapps.us/llm.txt</a>'
                                        ),
                                        cls="skill-line mb-2",
                                    ),
                                    P(
                                        "If you're a human: share these links with your agent.",
                                        cls="is-size-7 has-text-grey",
                                    ),
                                    id="llm",
                                    cls="mb-2",
                                ),
                                cls="box",
                            ),
                            cls="home-box p-6 mx-auto",
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
                            P(
                                NotStr(
                                    'API quick reference: <a href="https://mtlminiapps.us/llm.txt" target="_blank">https://mtlminiapps.us/llm.txt</a>'
                                ),
                                cls="is-size-7 has-text-grey mt-3",
                            ),
                            P(
                                NotStr(
                                    'Made by <a href="https://github.com/attid" target="_blank">Igor Tolstov</a> with support of <a href="https://mtla.me/en/" target="_blank">MTLA</a>'
                                ),
                                cls="is-size-7 has-text-grey mt-3",
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


def render_agents_fragment(
    agents: list[dict] | None = None,
    *,
    info: str | None = None,
    error: str | None = None,
) -> str:
    if error:
        return to_xml(P(error, cls="has-text-danger"))
    if info:
        return to_xml(P(info, cls="has-text-grey-light is-italic"))
    if not agents:
        return to_xml(P("Список агентов пуст", cls="has-text-grey-light is-italic"))

    cards = [P("Список агентов", cls="has-text-weight-semibold mb-3")]
    for agent in agents:
        agent_id = agent["id"]
        is_active = int(agent.get("is_active", 1)) == 1
        toggle_to = 0 if is_active else 1
        toggle_label = "Ban" if is_active else "Unban"
        toggle_class = "is-danger" if is_active else "is-success"
        cards.append(
            Div(
                Div(
                    Span(f"ID {agent_id}", cls="tag is-light"),
                    Span(agent["agent_id"], cls="ml-2 is-family-monospace"),
                    Span(
                        "active" if is_active else "banned",
                        cls=f"tag ml-2 {'is-success' if is_active else 'is-danger'} is-light",
                    ),
                    cls="mb-2",
                ),
                P(agent.get("name") or "", cls="is-size-7 has-text-grey mb-2"),
                Div(
                    Span(
                        f"Gen URL {agent.get('stateless_generated_count', 0)}",
                        cls="tag is-link is-light",
                    ),
                    Span(
                        f"View URL {agent.get('stateless_view_count', 0)}",
                        cls="tag is-warning is-light ml-1",
                    ),
                    Span(
                        f"Persist {agent.get('persistent_created_count', 0)}",
                        cls="tag is-success is-light ml-1",
                    ),
                    Span(
                        f"Apps {agent.get('apps_count', 0)}",
                        cls="tag is-info is-light ml-1",
                    ),
                    Span(
                        f"Tokens {agent.get('tokens_count', 0)}",
                        cls="tag is-info is-light ml-1",
                    ),
                    Span(
                        f"Seen {agent.get('last_seen_at') or '-'}",
                        cls="tag is-light ml-1",
                    ),
                    cls="mb-2",
                ),
                Div(
                    Input(
                        type="hidden",
                        id=f"agent-ref-{agent_id}",
                        name="agent_ref_id",
                        value=str(agent_id),
                    ),
                    Input(
                        type="hidden",
                        id=f"agent-active-{agent_id}",
                        name="is_active",
                        value=str(toggle_to),
                    ),
                    Button(
                        toggle_label,
                        cls=f"button is-small {toggle_class} is-light",
                        hx_post="/admin/fragments/agents/toggle",
                        hx_include=f"#key,#agent-ref-{agent_id},#agent-active-{agent_id}",
                        hx_target="#agents-list",
                        hx_swap="innerHTML",
                    ),
                    Button(
                        "Страницы",
                        cls="button is-small is-link is-light ml-2",
                        hx_get=f"/admin/fragments/agents/apps?agent_ref_id={agent_id}",
                        hx_include="#key",
                        hx_target=f"#agent-pages-{agent_id}",
                        hx_swap="innerHTML",
                    ),
                    cls="mb-2",
                ),
                Div(
                    id=f"agent-pages-{agent_id}",
                    cls="is-size-7 has-text-grey",
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
                                        Li(
                                            A(
                                                "Агенты",
                                                onclick="switchTab('agents')",
                                            ),
                                            id="tab-agents",
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
                            Div(
                                H1("Агенты", cls="title is-6 mt-4"),
                                Button(
                                    "Обновить агентов",
                                    id="refresh-agents-btn",
                                    cls="button is-light is-fullwidth mt-2",
                                    hx_get="/admin/fragments/agents",
                                    hx_include="#key",
                                    hx_target="#agents-list",
                                    hx_swap="innerHTML",
                                ),
                                Div(
                                    "Введите admin ключ для списка агентов",
                                    id="agents-list",
                                    cls="has-text-grey-light is-italic mt-3",
                                ),
                                id="content-agents",
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
