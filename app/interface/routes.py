import hmac
import hashlib
import logging
import base64
import gzip
import secrets
import string
import datetime as dt
from pathlib import Path
from typing import Optional

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
    get_app,
    get_users_stats,
    list_agent_apps,
    issue_agent_token,
    list_apps,
    list_users,
    log_action,
    save_app,
    save_agent_app,
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
    render_admin_page,
    render_apps_fragment,
    render_home_page,
    render_users_fragment,
)


def derive_agent_id(secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.b32encode(digest).decode("utf-8").rstrip("=")


def validate_agent_secret(secret: str) -> tuple[bool, str]:
    agent_id = derive_agent_id(secret)
    is_valid = (
        agent_id.startswith("MTL") and len(agent_id) >= 8 and agent_id[:8].isalpha()
    )
    return is_valid, agent_id


def generate_agent_slug() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def register_routes(
    app: FastAPI,
    default_secret: str,
    default_domain: str,
    agent_app_ttl_days: int = 7,
) -> None:
    app_dir = Path(__file__).resolve().parents[1]
    repo_dir = app_dir.parent

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

    def is_agent_app_expired(last_accessed_at: str | None) -> bool:
        if not last_accessed_at:
            return False
        try:
            ts = dt.datetime.fromisoformat(last_accessed_at)
        except ValueError:
            return False
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.UTC)
        expires_at = ts + dt.timedelta(days=agent_app_ttl_days)
        return dt.datetime.now(dt.UTC) > expires_at

    @app.get("/", response_class=HTMLResponse)
    async def run_app(
        request: Request, d: Optional[str] = None, s: Optional[str] = None
    ):
        if not d or not s:
            return HTMLResponse(content=render_home_page())

        users = list_users()
        matched_key = None
        matched_user_id = None

        key_map = {u["key"]: u["id"] for u in users}
        if default_secret not in key_map:
            key_map[default_secret] = 1

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

        key_prefix = matched_key[:5] if len(matched_key) >= 5 else matched_key
        logging.info(f"Access granted using key starting with: {key_prefix}")

        if matched_user_id:
            log_action(matched_user_id, "view_stateless")

        try:
            html_content = decompress_payload(d)
            return html_content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Decoding error: {str(e)}")

    @app.get("/p/{slug}", response_class=HTMLResponse)
    async def run_persistent_app_admin(slug: str):
        app_data = get_app(slug, user_id=1)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")

        log_action(1, "view_persistent", slug=slug)
        return HTMLResponse(content=app_data["html_content"])

    @app.get("/p{user_id}/{slug}", response_class=HTMLResponse)
    async def run_persistent_app_user(user_id: int, slug: str):
        app_data = get_app(slug, user_id=user_id)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")

        log_action(user_id, "view_persistent", slug=slug)
        return HTMLResponse(content=app_data["html_content"])

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page(request: Request):
        return HTMLResponse(content=render_admin_page())

    @app.get("/skill.md", response_class=PlainTextResponse)
    async def skill_md():
        path = app_dir / "public" / "skill.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="skill.md not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/markdown"
        )

    @app.get("/llm.txt", response_class=PlainTextResponse)
    async def llm_txt():
        path = app_dir / "public" / "llm.txt"
        if not path.exists():
            raise HTTPException(status_code=404, detail="llm.txt not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )

    @app.post("/api/agent/register")
    async def agent_register(req: AgentRegisterRequest):
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
        _ = agent

        raw_bytes = len(req.html.encode("utf-8"))
        if raw_bytes > 102400:
            raise HTTPException(status_code=400, detail="Raw HTML exceeds 100KB")

        html_to_process = req.html
        if req.compress:
            html_to_process = minify_html(html_to_process)

        payload = compress_payload(html_to_process)
        signature = sign_data(payload, default_secret)

        domain = req.domain if req.domain else default_domain
        domain = domain.rstrip("/")
        full_url = f"{domain}/?d={payload}&s={signature}"

        return {"url": full_url, "url_bytes": len(full_url)}

    @app.post("/api/agent/apps")
    async def agent_save_app(req: AgentSaveAppRequest, request: Request):
        agent = get_agent_from_bearer(request)
        raw_bytes = len(req.html.encode("utf-8"))
        if raw_bytes > 102400:
            raise HTTPException(status_code=400, detail="Raw HTML exceeds 100KB")

        slug = (req.slug or "").strip()
        if not slug:
            for _ in range(20):
                candidate = generate_agent_slug()
                if not get_agent_app(agent["id"], candidate):
                    slug = candidate
                    break
            if not slug:
                raise HTTPException(status_code=500, detail="Failed to generate slug")

        compressed = gzip.compress(req.html.encode("utf-8"))
        save_agent_app(
            agent_ref_id=agent["id"],
            slug=slug,
            html_content=compressed,
            content_encoding="gzip",
        )
        domain = default_domain.rstrip("/")
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

    @app.get("/a/{agent_id}/{slug}", response_class=HTMLResponse)
    async def run_agent_persistent_app(agent_id: str, slug: str):
        app_data = get_agent_app_by_agent_id(agent_id, slug)
        if not app_data:
            raise HTTPException(status_code=404, detail="App not found")
        if is_agent_app_expired(app_data.get("last_accessed_at")):
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

    @app.get("/scripts/register_agent.py", response_class=PlainTextResponse)
    async def register_agent_py():
        path = repo_dir / "scripts" / "register_agent.py"
        if not path.exists():
            raise HTTPException(status_code=404, detail="register_agent.py not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )

    @app.get("/scripts/register_agent.mjs", response_class=PlainTextResponse)
    async def register_agent_mjs():
        path = repo_dir / "scripts" / "register_agent.mjs"
        if not path.exists():
            raise HTTPException(status_code=404, detail="register_agent.mjs not found")
        return PlainTextResponse(
            path.read_text(encoding="utf-8"), media_type="text/plain"
        )

    @app.get("/admin/fragments/apps", response_class=HTMLResponse)
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

    @app.post("/admin/fragments/apps/save", response_class=HTMLResponse)
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

    @app.get("/admin/fragments/users", response_class=HTMLResponse)
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

    @app.post("/admin/fragments/users/create", response_class=HTMLResponse)
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

    @app.post("/api/generate")
    async def generate_api(req: GenerateRequest):
        user = get_current_user_by_key(req.key, default_secret)

        html_to_process = req.html
        if req.compress:
            html_to_process = minify_html(html_to_process)

        payload = compress_payload(html_to_process)
        signature = sign_data(payload, req.key)

        domain = req.domain if req.domain else default_domain
        domain = domain.rstrip("/")

        full_url = f"{domain}/?d={payload}&s={signature}"

        log_action(user["id"], "generate")
        return {"url": full_url}

    @app.post("/api/apps")
    async def save_app_api(req: SaveAppRequest):
        user = get_current_user_by_key(req.key, default_secret)

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

    @app.post("/api/users")
    async def create_user_api(req: CreateUserRequest):
        admin = get_current_user_by_key(req.admin_key, default_secret)
        if admin["id"] != 1:
            raise HTTPException(status_code=403, detail="Only Admin can create users")

        try:
            new_id = create_user(req.key, req.comment)
            return {"id": new_id, "key": req.key}
        except ValueError:
            raise HTTPException(status_code=400, detail="Key already exists")

    @app.get("/api/users")
    async def list_users_api(key: str):
        user = get_current_user_by_key(key, default_secret)
        if user["id"] != 1:
            raise HTTPException(status_code=403, detail="Only Admin can list users")

        return with_user_stats(list_users())
