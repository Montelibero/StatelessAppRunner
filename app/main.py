import logging
import os
import secrets

from fastapi import FastAPI, Request

from application.payload import (
    compress_payload,
    decompress_payload,
    minify_html,
    remove_js_comments,
    sign_data,
)
from db import init_db, sync_admin_key
from interface.routes import register_routes

app = FastAPI(title="Stateless App Runner")


def get_agent_app_ttl_days() -> int:
    raw = os.getenv("AGENT_APP_TTL_DAYS", "7").strip()
    try:
        value = int(raw)
    except ValueError:
        return 7
    return value if value > 0 else 7


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    query_params = request.query_params

    is_runner = path.startswith("/p") or (
        path == "/" and "d" in query_params and "s" in query_params
    )

    if is_runner:
        response.headers["Content-Security-Policy"] = (
            "default-src * 'unsafe-inline' 'unsafe-eval'; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline' 'unsafe-eval'; img-src * data:; font-src *; connect-src *; frame-ancestors *;"
        )
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://unpkg.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net https://unpkg.com 'unsafe-inline'; "
            "font-src 'self' https://unpkg.com https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net; "
            "frame-ancestors 'self';"
        )
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


init_db()

DEFAULT_SECRET = os.getenv("SECRET_KEY")
if not DEFAULT_SECRET:
    DEFAULT_SECRET = secrets.token_urlsafe(32)
    logging.warning(f"No SECRET_KEY set. Generated random secret: {DEFAULT_SECRET}")

sync_admin_key(DEFAULT_SECRET)

DEFAULT_DOMAIN = os.getenv("APP_DOMAIN", "https://mtlminiapps.us")
AGENT_APP_TTL_DAYS = get_agent_app_ttl_days()
AGENT_MAX_PERSIST_APPS = _get_env_int("AGENT_MAX_PERSIST_APPS", 80)
AGENT_MAX_PERSIST_BYTES = _get_env_int("AGENT_MAX_PERSIST_BYTES", 5_000_000)
AGENT_CREATE_RATE_PER_MIN = _get_env_int("AGENT_CREATE_RATE_PER_MIN", 5)
AGENT_CREATE_RATE_PER_HOUR = _get_env_int("AGENT_CREATE_RATE_PER_HOUR", 20)
AGENT_CREATE_RATE_PER_DAY = _get_env_int("AGENT_CREATE_RATE_PER_DAY", 40)

register_routes(
    app,
    default_secret=DEFAULT_SECRET,
    default_domain=DEFAULT_DOMAIN,
    agent_app_ttl_days=AGENT_APP_TTL_DAYS,
    agent_max_persist_apps=AGENT_MAX_PERSIST_APPS,
    agent_max_persist_bytes=AGENT_MAX_PERSIST_BYTES,
    agent_create_rate_per_min=AGENT_CREATE_RATE_PER_MIN,
    agent_create_rate_per_hour=AGENT_CREATE_RATE_PER_HOUR,
    agent_create_rate_per_day=AGENT_CREATE_RATE_PER_DAY,
)

__all__ = [
    "app",
    "DEFAULT_SECRET",
    "DEFAULT_DOMAIN",
    "AGENT_APP_TTL_DAYS",
    "get_agent_app_ttl_days",
    "sign_data",
    "compress_payload",
    "decompress_payload",
    "remove_js_comments",
    "minify_html",
]
