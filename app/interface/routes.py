import hmac
import hashlib
import logging
import base64
import gzip
import secrets
import string
import datetime as dt
import os
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from application.auth import get_current_user_by_key
from application.payload import (
    compress_payload,
    decompress_payload,
    minify_html,
    sign_data,
)
from db import (
    create_user,
    create_or_get_agent,
    delete_app,
    delete_agent_app,
    get_agent_by_agent_id,
    get_agent_app,
    get_agent_app_by_agent_id,
    get_agent_by_token,
    get_agent_persist_usage,
    get_app,
    get_users_stats,
    list_agent_apps,
    issue_agent_token,
    list_agents_with_stats,
    list_apps,
    list_users,
    count_agent_actions_since,
    log_agent_action,
    log_action,
    get_user_by_id,
    get_agent_by_id,
    save_app,
    save_agent_app,
    set_user_active,
    set_agent_active,
    touch_agent_app_access,
)
from interface.schemas import (
    AgentSaveAppRequest,
    CreateUserRequest,
    DeleteAppRequest,
    AgentGenerateRequest,
    AgentRegisterRequest,
    GenerateRequest,
    SaveAppRequest,
)
from ui.pages import (
    render_agents_fragment,
    render_admin_page,
    render_apps_fragment,
    render_home_page,
    render_terms_page,
    render_users_fragment,
)


def derive_agent_id(secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    # Deterministic ID without brute-force search: stable MTLA prefix + hash body.
    body = base64.b32encode(digest).decode("utf-8").rstrip("=")
    return f"MTLA{body[4:]}"


def validate_agent_secret(secret: str) -> tuple[bool, str]:
    agent_id = derive_agent_id(secret)
    if not secret.strip():
        return False, agent_id
    return True, agent_id


def generate_agent_slug() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _leading_zero_bits(data: bytes) -> int:
    bits = 0
    for b in data:
        if b == 0:
            bits += 8
            continue
        return bits + (8 - b.bit_length())
    return bits


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + pad).encode("utf-8"))


def make_pow_challenge(secret_key: str, bits: int, ttl_seconds: int) -> tuple[str, str]:
    expires_ts = int(dt.datetime.now(dt.UTC).timestamp()) + ttl_seconds
    payload = {"n": secrets.token_urlsafe(16), "b": bits, "e": expires_ts}
    payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    payload_b64 = _b64url(payload_raw)
    sig = hmac.new(
        secret_key.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{sig}", dt.datetime.fromtimestamp(
        expires_ts, tz=dt.UTC
    ).isoformat()


def parse_pow_challenge(secret_key: str, challenge: str) -> Optional[dict]:
    if "." not in challenge:
        return None
    payload_b64, sig = challenge.split(".", 1)
    expected_sig = hmac.new(
        secret_key.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for key in ("n", "b", "e"):
        if key not in payload:
            return None
    try:
        bits = int(payload["b"])
        expires = int(payload["e"])
    except (TypeError, ValueError):
        return None
    now_ts = int(dt.datetime.now(dt.UTC).timestamp())
    if expires < now_ts:
        return None
    if bits < 1:
        return None
    payload["b"] = bits
    payload["e"] = expires
    return payload


def verify_registration_pow(
    agent_secret: str, pow_challenge: str, pow_nonce: str, secret_key: str
) -> bool:
    payload = parse_pow_challenge(secret_key, pow_challenge)
    if not payload:
        return False
    bits = int(payload["b"])
    seed = str(payload["n"])
    payload_bytes = f"{seed}:{agent_secret}:{pow_nonce}".encode("utf-8")
    digest = hashlib.sha256(payload_bytes).digest()
    return _leading_zero_bits(digest) >= bits


def _normalize_domain(domain: str) -> str:
    raw = domain.strip()
    if not raw:
        return raw
    parsed = urlparse(raw)
    if not parsed.scheme:
        parsed = urlparse(f"https://{raw}")
    host = (parsed.hostname or "").lower()
    scheme = parsed.scheme.lower()
    if (
        scheme == "http"
        and host not in {"localhost", "127.0.0.1"}
        and not host.endswith(".local")
    ):
        parsed = parsed._replace(scheme="https")
    normalized = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path or "",
            "",
            "",
            "",
        )
    )
    return normalized.rstrip("/")


def register_routes(
    app: FastAPI,
    default_secret: str,
    default_domain: str,
    agent_app_ttl_days: int = 7,
    agent_max_persist_apps: int = 80,
    agent_max_persist_bytes: int = 5_000_000,
    agent_create_rate_per_min: int = 5,
    agent_create_rate_per_hour: int = 20,
    agent_create_rate_per_day: int = 40,
) -> None:
    app_dir = Path(__file__).resolve().parents[1]

    def _read_registration_script(filename: str) -> str:
        path = app_dir / "public" / "skill" / "scripts" / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        raise HTTPException(status_code=404, detail=f"{filename} not found")

    def with_user_stats(users: list[dict]) -> list[dict]:
        stats = get_users_stats()
        for user in users:
            uid = user["id"]
            user["stats"] = stats.get(
                uid,
                {
                    "generated": 0,
                    "view_stateless": 0,
                    "view_persistent": 0,
                    "apps_count": 0,
                },
            )
        return users

    def apps_for_user(user_id: int) -> list[dict]:
        if user_id == 1:
            return list_apps(user_id=None)
        return list_apps(user_id=user_id)

    def get_agent_from_bearer(request: Request) -> dict:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token = header[len("Bearer ") :].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        agent = get_agent_by_token(token)
        if not agent:
            raise HTTPException(status_code=403, detail="Invalid bearer token")
        return agent

    def is_agent_app_expired(app_data: dict) -> bool:
        ts_candidates = []
        for key in ("last_accessed_at", "updated_at"):
            val = app_data.get(key)
            if val:
                try:
                    ts = dt.datetime.fromisoformat(val)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=dt.UTC)
                    ts_candidates.append(ts)
                except ValueError:
                    pass
        if not ts_candidates:
            return False

        latest_ts = max(ts_candidates)
        expires_at = latest_ts + dt.timedelta(days=agent_app_ttl_days)
        return dt.datetime.now(dt.UTC) > expires_at

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def run_app(
        request: Request,
        d: Optional[str] = None,
        s: Optional[str] = None,
        a: Optional[str] = None,
    ):
        if not d or not s:
            return HTMLResponse(content=render_home_page())

        users = list_users()
        matched_key = None
        matched_user_id = None

        key_map = {u["key"]: u["id"] for u in users}
        if default_secret not in key_map:
            key_map[default_secret] = 1

        if a:
            for key, uid in key_map.items():
                expected_sign = sign_data(f"{d}:{a}", key)
                if hmac.compare_digest(expected_sign, s):
                    matched_key = key
                    matched_user_id = uid
                    break
        else:
            for key, uid in key_map.items():
                expected_sign = sign_data(d, key)
                if hmac.compare_digest(expected_sign, s):
                    matched_key = key
                    matched_user_id = uid
                    break

        if not matched_key:
            raise HTTPException(
                status_code=403, detail="Integrity Check Failed (Invalid Signature)"
            )

        if matched_user_id and matched_user_id != 1:
            owner_user = get_user_by_id(matched_user_id)
            if not owner_user or int(owner_user.get("is_active", 1)) != 1:
                raise HTTPException(status_code=403, detail="User link is inactive")

        linked_agent = None
        if a:
            linked_agent = get_agent_by_agent_id(a)
            if not linked_agent or linked_agent.get("is_active") != 1:
                raise HTTPException(status_code=403, detail="Agent link is inactive")

        key_prefix = matched_key[:5] if len(matched_key) >= 5 else matched_key
        logging.info(f"Access granted using key starting with: {key_prefix}")

        if matched_user_id:
            log_action(matched_user_id, "view_stateless")
        if linked_agent:
            log_agent_action(linked_agent["id"], "view_stateless")

        try:
            html_content = decompress_payload(d)
            return html_content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Decoding error: {str(e)}")

    @app.get("/p/{slug}", response_class=HTMLResponse, include_in_schema=False)
    async def run_persistent_app_admin(slug: str):
        app_data = get_app(slug, user_id=1)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")

        log_action(1, "view_persistent", slug=slug)
        return HTMLResponse(content=app_data["html_content"])

    @app.get("/p{user_id}/{slug}", response_class=HTMLResponse, include_in_schema=False)
    async def run_persistent_app_user(user_id: int, slug: str):
        owner_user = get_user_by_id(user_id)
        if not owner_user or int(owner_user.get("is_active", 1)) != 1:
            raise HTTPException(status_code=404, detail="App not found")
        app_data = get_app(slug, user_id=user_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")

        log_action(user_id, "view_persistent", slug=slug)
        return HTMLResponse(content=app_data["html_content"])

    @app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
    async def admin_page(request: Request):
        return HTMLResponse(content=render_admin_page())

    @app.get("/skill.md", response_class=PlainTextResponse, include_in_schema=False)
    async def skill_md():
        path = app_dir / "public" / "skill" / "SKILL.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="skill.md not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/markdown"
        )

    @app.get("/llm.txt", response_class=PlainTextResponse, include_in_schema=False)
    async def llm_txt():
        path = app_dir / "public" / "llm.txt"
        if not path.exists():
            raise HTTPException(status_code=404, detail="llm.txt not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )

    @app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
    async def terms_page():
        return HTMLResponse(content=render_terms_page())

    @app.post("/api/agent/register/challenge")
    async def agent_register_challenge():
        bits_raw = os.getenv("AGENT_REGISTER_POW_BITS", "24").strip()
        ttl_raw = os.getenv("AGENT_REGISTER_POW_TTL_SECONDS", "300").strip()
        try:
            bits = int(bits_raw)
        except ValueError:
            bits = 24
        try:
            ttl_seconds = int(ttl_raw)
        except ValueError:
            ttl_seconds = 300
        if bits < 1:
            bits = 1
        if ttl_seconds < 30:
            ttl_seconds = 30
        challenge, expires_at = make_pow_challenge(default_secret, bits, ttl_seconds)
        return {
            "pow_challenge": challenge,
            "pow_bits": bits,
            "expires_at": expires_at,
        }

    @app.post("/api/agent/register")
    async def agent_register(req: AgentRegisterRequest):
        if not req.pow_challenge or not req.pow_nonce:
            raise HTTPException(status_code=400, detail="Agent PoW failed")
        if not verify_registration_pow(
            req.agent_secret, req.pow_challenge, req.pow_nonce, default_secret
        ):
            raise HTTPException(status_code=400, detail="Agent PoW failed")

        is_valid, agent_id = validate_agent_secret(req.agent_secret)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Agent challenge failed")

        existed = get_agent_by_agent_id(agent_id) is not None
        agent = create_or_get_agent(
            agent_id=agent_id,
            secret=req.agent_secret,
            name=req.agent_name,
        )
        bearer_token = issue_agent_token(agent["id"])
        return {
            "agent_id": agent["agent_id"],
            "bearer_token": bearer_token,
            "created": not existed,
        }

    @app.get("/api/agent/me")
    async def agent_me(request: Request):
        agent = get_agent_from_bearer(request)
        return {
            "id": agent["id"],
            "agent_id": agent["agent_id"],
            "name": agent.get("name"),
        }

    @app.post("/api/agent/generate")
    async def agent_generate(req: AgentGenerateRequest, request: Request):
        agent = get_agent_from_bearer(request)
        if not req.html.strip():
            raise HTTPException(status_code=400, detail="HTML cannot be empty")

        raw_bytes = len(req.html.encode("utf-8"))
        if raw_bytes > 102400:
            raise HTTPException(status_code=400, detail="Raw HTML exceeds 100KB")

        html_to_process = req.html
        if req.compress:
            html_to_process = minify_html(html_to_process)

        payload = compress_payload(html_to_process)
        signature = sign_data(f"{payload}:{agent['agent_id']}", default_secret)

        domain = (
            _normalize_domain(req.domain)
            if req.domain
            else _normalize_domain(default_domain)
        )
        full_url = f"{domain}/?d={payload}&s={signature}&a={agent['agent_id']}"

        log_agent_action(agent["id"], "generate_stateless")

        return {"url": full_url, "url_bytes": len(full_url)}

    @app.post("/api/agent/apps")
    async def agent_save_app(req: AgentSaveAppRequest, request: Request):
        agent = get_agent_from_bearer(request)
        if not req.html.strip():
            raise HTTPException(status_code=400, detail="HTML cannot be empty")
        raw_bytes = len(req.html.encode("utf-8"))
        if raw_bytes > 102400:
            raise HTTPException(status_code=400, detail="Raw HTML exceeds 100KB")

        slug = (req.slug or "").strip()
        existed_before = False
        if slug:
            existed_before = get_agent_app(agent["id"], slug) is not None
        if not slug:
            for _ in range(20):
                candidate = generate_agent_slug()
                if not get_agent_app(agent["id"], candidate):
                    slug = candidate
                    break
            if not slug:
                raise HTTPException(status_code=500, detail="Failed to generate slug")

        if not existed_before:
            usage = get_agent_persist_usage(agent["id"])
            if usage["apps_count"] >= agent_max_persist_apps:
                raise HTTPException(
                    status_code=409, detail="Agent app count limit exceeded"
                )
            now = dt.datetime.now(dt.UTC)
            since_min = (now - dt.timedelta(minutes=1)).isoformat()
            since_hour = (now - dt.timedelta(hours=1)).isoformat()
            since_day = (now - dt.timedelta(days=1)).isoformat()

            per_min = count_agent_actions_since(
                agent["id"], "create_persistent", since_min
            )
            if per_min >= agent_create_rate_per_min:
                raise HTTPException(
                    status_code=429, detail="Create rate per minute exceeded"
                )

            per_hour = count_agent_actions_since(
                agent["id"], "create_persistent", since_hour
            )
            if per_hour >= agent_create_rate_per_hour:
                raise HTTPException(
                    status_code=429, detail="Create rate per hour exceeded"
                )

            per_day = count_agent_actions_since(
                agent["id"], "create_persistent", since_day
            )
            if per_day >= agent_create_rate_per_day:
                raise HTTPException(
                    status_code=429, detail="Create rate per day exceeded"
                )
        else:
            now = dt.datetime.now(dt.UTC)
            since_min = (now - dt.timedelta(minutes=1)).isoformat()
            per_min_updates = count_agent_actions_since(
                agent["id"], "update_persistent", since_min
            )
            if per_min_updates >= agent_create_rate_per_min:
                raise HTTPException(
                    status_code=429, detail="Edit rate per minute exceeded"
                )

        compressed = gzip.compress(req.html.encode("utf-8"))
        usage_after = get_agent_persist_usage(agent["id"])
        existing = get_agent_app(agent["id"], slug)
        old_bytes = 0
        if existing and existing.get("html_content") is not None:
            payload_old = existing["html_content"]
            if isinstance(payload_old, bytes):
                old_bytes = len(payload_old)
            else:
                old_bytes = len(str(payload_old).encode("utf-8"))

        projected_total = usage_after["bytes_total"] - old_bytes + len(compressed)
        if projected_total > agent_max_persist_bytes:
            raise HTTPException(status_code=409, detail="Agent storage limit exceeded")

        save_agent_app(
            agent_ref_id=agent["id"],
            slug=slug,
            html_content=compressed,
            content_encoding="gzip",
        )
        if not existed_before:
            log_agent_action(agent["id"], "create_persistent", slug=slug)
        else:
            log_agent_action(agent["id"], "update_persistent", slug=slug)
        domain = _normalize_domain(default_domain)
        return {"slug": slug, "url": f"{domain}/a/{agent['agent_id']}/{slug}"}

    @app.get("/api/agent/apps")
    async def agent_list_apps(request: Request):
        agent = get_agent_from_bearer(request)
        return list_agent_apps(agent["id"])

    @app.delete("/api/agent/apps/{slug}")
    async def agent_delete_app(slug: str, request: Request):
        agent = get_agent_from_bearer(request)
        delete_agent_app(agent["id"], slug)
        return {"status": "deleted", "slug": slug}

    @app.get(
        "/a/{agent_id}/{slug}", response_class=HTMLResponse, include_in_schema=False
    )
    async def run_agent_persistent_app(agent_id: str, slug: str):
        app_data = get_agent_app_by_agent_id(agent_id, slug)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")
        owner = get_agent_by_id(app_data["agent_ref_id"])
        if not owner or owner.get("is_active") != 1:
            raise HTTPException(status_code=404, detail="App not found")
        if is_agent_app_expired(app_data):
            raise HTTPException(status_code=404, detail="App expired")

        payload = app_data["html_content"]
        if app_data.get("content_encoding") == "gzip":
            html = gzip.decompress(payload).decode("utf-8")
        else:
            if isinstance(payload, bytes):
                html = payload.decode("utf-8")
            else:
                html = str(payload)

        touch_agent_app_access(app_data["agent_ref_id"], slug)
        return HTMLResponse(content=html)

    @app.get(
        "/scripts/register_agent.py",
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
    async def register_agent_py():
        return PlainTextResponse(
            _read_registration_script("register_agent.py"),
            media_type="text/plain",
        )

    @app.get(
        "/scripts/register_agent.mjs",
        response_class=PlainTextResponse,
        include_in_schema=False,
    )
    async def register_agent_mjs():
        return PlainTextResponse(
            _read_registration_script("register_agent.mjs"),
            media_type="text/plain",
        )

    @app.get(
        "/admin/fragments/apps", response_class=HTMLResponse, include_in_schema=False
    )
    async def admin_apps_fragment(key: str = ""):
        if not key.strip():
            return HTMLResponse(
                content=render_apps_fragment(
                    info="Введите ключ чтобы увидеть приложения..."
                )
            )

        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_apps_fragment(error="Неверный ключ"))

        return HTMLResponse(content=render_apps_fragment(apps_for_user(user["id"])))

    @app.post(
        "/admin/fragments/apps/save",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def admin_apps_save_fragment(
        key: str = Form(""),
        slug: str = Form(""),
        html: str = Form(""),
    ):
        if not key.strip():
            return HTMLResponse(content=render_apps_fragment(error="Нужен ключ"))
        if not slug.strip():
            return HTMLResponse(content=render_apps_fragment(error="Нужно имя ссылки"))

        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_apps_fragment(error="Неверный ключ"))

        save_app(slug.strip(), html, user_id=user["id"])
        apps = apps_for_user(user["id"])
        return HTMLResponse(content=render_apps_fragment(apps))

    @app.get(
        "/admin/fragments/users", response_class=HTMLResponse, include_in_schema=False
    )
    async def admin_users_fragment(key: str = ""):
        if not key.strip():
            return HTMLResponse(
                content=render_users_fragment(
                    info="Введите admin ключ для списка пользователей"
                )
            )

        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_users_fragment(error="Неверный ключ"))
        if user["id"] != 1:
            return HTMLResponse(
                content=render_users_fragment(
                    error="Только admin может видеть пользователей"
                )
            )

        return HTMLResponse(
            content=render_users_fragment(with_user_stats(list_users()))
        )

    @app.get(
        "/admin/fragments/agents", response_class=HTMLResponse, include_in_schema=False
    )
    async def admin_agents_fragment(key: str = ""):
        if not key.strip():
            return HTMLResponse(
                content=render_agents_fragment(
                    info="Введите admin ключ для списка агентов"
                )
            )

        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_agents_fragment(error="Неверный ключ"))
        if user["id"] != 1:
            return HTMLResponse(
                content=render_agents_fragment(
                    error="Только admin может видеть агентов"
                )
            )

        return HTMLResponse(content=render_agents_fragment(list_agents_with_stats()))

    @app.get(
        "/admin/fragments/agents/apps",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def admin_agents_apps_fragment(key: str = "", agent_ref_id: int = 0):
        if not key.strip():
            return HTMLResponse(
                content=render_agents_fragment(error="Нужен admin ключ")
            )
        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_agents_fragment(error="Неверный ключ"))
        if user["id"] != 1:
            return HTMLResponse(
                content=render_agents_fragment(
                    error="Только admin может видеть агентов"
                )
            )
        if agent_ref_id <= 0:
            return HTMLResponse(content=render_agents_fragment(error="Неверный агент"))
        apps = list_agent_apps(agent_ref_id)
        owner = get_agent_by_id(agent_ref_id)
        if not owner:
            return HTMLResponse(content=render_agents_fragment(error="Неверный агент"))
        if not apps:
            return HTMLResponse(content="Список пуст")
        lines = []
        for app_item in apps:
            slug = app_item["slug"]
            lines.append(
                f'<div class="mb-2"><a href="/a/{owner["agent_id"]}/{slug}" target="_blank">{slug}</a> <span class="is-size-7 has-text-grey">{app_item.get("html_bytes", 0)} B</span></div>'
            )
        return HTMLResponse(content="".join(lines))

    @app.post(
        "/admin/fragments/agents/toggle",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def admin_agents_toggle_fragment(
        key: str = Form(""),
        agent_ref_id: int = Form(0),
        is_active: int = Form(1),
    ):
        if not key.strip():
            return HTMLResponse(
                content=render_agents_fragment(error="Нужен admin ключ")
            )
        try:
            user = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_agents_fragment(error="Неверный ключ"))
        if user["id"] != 1:
            return HTMLResponse(
                content=render_agents_fragment(
                    error="Только admin может видеть агентов"
                )
            )
        if agent_ref_id <= 0:
            return HTMLResponse(content=render_agents_fragment(error="Неверный агент"))
        set_agent_active(agent_ref_id, is_active == 1)
        return HTMLResponse(content=render_agents_fragment(list_agents_with_stats()))

    @app.post(
        "/admin/fragments/users/create",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def admin_users_create_fragment(
        key: str = Form(""),
        new_user_key: str = Form(""),
        new_user_comment: str = Form(""),
    ):
        if not key.strip():
            return HTMLResponse(content=render_users_fragment(error="Нужен admin ключ"))
        if not new_user_key.strip():
            return HTMLResponse(content=render_users_fragment(error="Нужен новый ключ"))

        try:
            admin = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_users_fragment(error="Неверный ключ"))
        if admin["id"] != 1:
            return HTMLResponse(
                content=render_users_fragment(
                    error="Только admin может создавать пользователей"
                )
            )

        try:
            create_user(new_user_key.strip(), new_user_comment.strip())
        except ValueError:
            return HTMLResponse(
                content=render_users_fragment(error="Ключ уже существует")
            )

        return HTMLResponse(
            content=render_users_fragment(with_user_stats(list_users()))
        )

    @app.post(
        "/admin/fragments/users/toggle",
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    async def admin_users_toggle_fragment(
        key: str = Form(""),
        user_id: int = Form(0),
        is_active: int = Form(1),
    ):
        if not key.strip():
            return HTMLResponse(content=render_users_fragment(error="Нужен admin ключ"))
        try:
            admin = get_current_user_by_key(key, default_secret)
        except HTTPException:
            return HTMLResponse(content=render_users_fragment(error="Неверный ключ"))
        if admin["id"] != 1:
            return HTMLResponse(
                content=render_users_fragment(
                    error="Только admin может управлять пользователями"
                )
            )
        if user_id <= 0:
            return HTMLResponse(
                content=render_users_fragment(error="Неверный пользователь")
            )
        if user_id == 1:
            return HTMLResponse(
                content=render_users_fragment(error="Admin нельзя банить")
            )

        set_user_active(user_id, is_active == 1)
        return HTMLResponse(
            content=render_users_fragment(with_user_stats(list_users()))
        )

    @app.post("/api/generate")
    async def generate_api(req: GenerateRequest):
        user = get_current_user_by_key(req.key, default_secret)
        if not req.html.strip():
            raise HTTPException(status_code=400, detail="HTML cannot be empty")

        html_to_process = req.html
        if req.compress:
            html_to_process = minify_html(html_to_process)

        payload = compress_payload(html_to_process)
        signature = sign_data(payload, req.key)

        domain = (
            _normalize_domain(req.domain)
            if req.domain
            else _normalize_domain(default_domain)
        )

        full_url = f"{domain}/?d={payload}&s={signature}"

        log_action(user["id"], "generate")
        return {"url": full_url}

    @app.post("/api/apps")
    async def save_app_api(req: SaveAppRequest):
        user = get_current_user_by_key(req.key, default_secret)
        if not req.html.strip():
            raise HTTPException(status_code=400, detail="HTML cannot be empty")

        target_user_id = user["id"]
        if req.owner_id is not None:
            if user["id"] != 1:
                raise HTTPException(
                    status_code=403, detail="Only Admin can save to other users"
                )
            target_user_id = req.owner_id

        if not req.slug.strip():
            raise HTTPException(status_code=400, detail="Slug cannot be empty")

        save_app(req.slug.strip(), req.html, user_id=target_user_id)
        return {"status": "ok", "slug": req.slug, "user_id": target_user_id}

    @app.get("/api/apps")
    async def list_apps_api(key: str):
        user = get_current_user_by_key(key, default_secret)

        if user["id"] == 1:
            apps = list_apps(user_id=None)
        else:
            apps = list_apps(user_id=user["id"])

        return apps

    @app.get("/api/apps/{slug}")
    async def get_app_api(slug: str, key: str, target_user_id: Optional[int] = None):
        user = get_current_user_by_key(key, default_secret)

        uid = user["id"]
        if target_user_id is not None:
            if user["id"] != 1 and target_user_id != user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            uid = target_user_id

        app_data = get_app(slug, user_id=uid)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")
        return app_data

    @app.delete("/api/apps/{slug}")
    async def delete_app_api(
        slug: str, req: DeleteAppRequest, target_user_id: Optional[int] = None
    ):
        user = get_current_user_by_key(req.key, default_secret)

        uid = user["id"]
        req_target = req.owner_id if req.owner_id is not None else target_user_id

        if req_target is not None:
            if user["id"] != 1 and req_target != user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            uid = req_target

        delete_app(slug, user_id=uid)
        return {"status": "deleted", "slug": slug}

    @app.post("/api/users", include_in_schema=False)
    async def create_user_api(req: CreateUserRequest):
        admin = get_current_user_by_key(req.admin_key, default_secret)
        if admin["id"] != 1:
            raise HTTPException(status_code=403, detail="Only Admin can create users")

        try:
            new_id = create_user(req.key, req.comment)
            return {"id": new_id, "key": req.key}
        except ValueError:
            raise HTTPException(status_code=400, detail="Key already exists")

    @app.get("/api/users", include_in_schema=False)
    async def list_users_api(key: str):
        user = get_current_user_by_key(key, default_secret)
        if user["id"] != 1:
            raise HTTPException(status_code=403, detail="Only Admin can list users")

        return with_user_stats(list_users())
