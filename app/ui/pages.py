import os
import re

from fasthtml.common import Body, Head, Html, NotStr, to_xml


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES_DIR = os.path.join(_BASE_DIR, "templates")


_HEAD_RE = re.compile(r"<head>(.*?)</head>", re.DOTALL | re.IGNORECASE)
_BODY_RE = re.compile(r"<body>(.*?)</body>", re.DOTALL | re.IGNORECASE)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)


def _load_template(name: str) -> str:
    path = os.path.join(_TEMPLATES_DIR, name)
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _extract_parts(html: str) -> tuple[str, str]:
    head_match = _HEAD_RE.search(html)
    body_match = _BODY_RE.search(html)
    if not head_match or not body_match:
        raise ValueError("Template must contain <head> and <body>")

    head_inner = head_match.group(1)
    body_inner = body_match.group(1)

    # FastHTML renders <title> itself when present in head; keep exactly one title.
    head_inner = _TITLE_RE.sub("", head_inner)
    return head_inner, body_inner


def _render_from_template(template_name: str) -> str:
    raw = _load_template(template_name)
    head_inner, body_inner = _extract_parts(raw)
    return to_xml(
        Html(
            Head(NotStr(head_inner)),
            Body(NotStr(body_inner)),
            lang="ru",
        )
    )


def render_home_page() -> str:
    return _render_from_template("index.html")


def render_admin_page() -> str:
    return _render_from_template("admin.html")
