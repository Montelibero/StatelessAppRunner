import hmac
import logging
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from application.auth import get_current_user_by_key
from application.payload import (
    compress_payload,
    decompress_payload,
    minify_html,
    sign_data,
)
from db import (
    create_user,
    delete_app,
    get_app,
    get_users_stats,
    list_apps,
    list_users,
    log_action,
    save_app,
)
from interface.schemas import (
    CreateUserRequest,
    DeleteAppRequest,
    GenerateRequest,
    SaveAppRequest,
)
from ui.pages import (
    render_admin_page,
    render_apps_fragment,
    render_home_page,
    render_users_fragment,
)


def register_routes(app: FastAPI, default_secret: str, default_domain: str) -> None:
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
