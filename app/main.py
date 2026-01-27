import os
import zlib
import base64
import hmac
import hashlib
import secrets
import logging
import re
import uuid
from typing import Optional, List

from fastapi import FastAPI, Request, HTTPException, Form, Depends, Header
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from db import (
    init_db, save_app, get_app, list_apps, delete_app,
    sync_admin_key, get_user_by_key, create_user, list_users,
    log_action, get_users_stats
)

app = FastAPI(title="Stateless App Runner")

# Ensure DB is initialized
init_db()

# Default Secret (Admin Key)
DEFAULT_SECRET = os.getenv("SECRET_KEY")
if not DEFAULT_SECRET:
    DEFAULT_SECRET = secrets.token_urlsafe(32)
    logging.warning(f"No SECRET_KEY set. Generated random secret: {DEFAULT_SECRET}")

# Sync Admin Key to DB
sync_admin_key(DEFAULT_SECRET)

DEFAULT_DOMAIN = os.getenv("APP_DOMAIN", "https://mtlminiapps.us")

# --- CORE LOGIC ---

def sign_data(data: str, key: str) -> str:
    key_bytes = key.encode('utf-8')
    return hmac.new(key_bytes, data.encode('utf-8'), hashlib.sha256).hexdigest()

def compress_payload(html: str) -> str:
    compressed = zlib.compress(html.encode('utf-8'), level=9)
    return base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')

def decompress_payload(payload: str) -> str:
    padding = 4 - (len(payload) % 4)
    if padding != 4:
        payload += '=' * padding
    compressed_data = base64.urlsafe_b64decode(payload)
    return zlib.decompress(compressed_data).decode('utf-8')

def remove_js_comments(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    in_quote = None
    while i < n:
        char = text[i]
        if in_quote:
            if char == in_quote:
                escaped = False
                j = i - 1
                backslashes = 0
                while j >= 0 and text[j] == '\\':
                    backslashes += 1
                    j -= 1
                if backslashes % 2 == 0:
                    in_quote = None
            out.append(char)
            i += 1
            continue
        if char in ('"', "'", '`'):
            in_quote = char
            out.append(char)
            i += 1
            continue
        if char == '/' and i + 1 < n and text[i+1] == '/':
            i += 2
            while i < n and text[i] != '\n':
                i += 1
            continue
        out.append(char)
        i += 1
    return "".join(out)

def minify_html(html_content: str) -> str:
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    def process_script(match):
        return match.group(1) + remove_js_comments(match.group(2)) + match.group(3)
    html_content = re.sub(r'(<script[^>]*>)(.*?)(</script>)', process_script, html_content, flags=re.DOTALL | re.IGNORECASE)
    def process_style(match):
        content = re.sub(r'/\*.*?\*/', '', match.group(2), flags=re.DOTALL)
        return match.group(1) + content + match.group(3)
    html_content = re.sub(r'(<style[^>]*>)(.*?)(</style>)', process_style, html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'\s+', ' ', html_content)
    return html_content.strip()

# --- AUTH HELPER ---

def get_current_user_by_key(key: str):
    user = get_user_by_key(key)
    if not user:
        if key == DEFAULT_SECRET:
             return {"id": 1, "key": DEFAULT_SECRET, "comment": "Admin (Fallback)"}
        raise HTTPException(status_code=403, detail="Invalid Key")
    return user

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def run_app(request: Request, d: str = None, s: str = None):
    if not d or not s:
        return templates.TemplateResponse(request=request, name="index.html")

    users = list_users()
    matched_key = None
    matched_user_id = None

    # We need to find the specific user who owns the key for stats
    # Optimization: Iterate users and check signature
    # Also check DEFAULT_SECRET explicitly

    # Check default secret first?
    # If DEFAULT_SECRET is not in DB users for some reason, we treat it as Admin (ID 1)
    # But sync_admin_key should handle it.

    # Build map key->user_id
    key_map = {u['key']: u['id'] for u in users}

    # If DEFAULT_SECRET not in map (e.g. env var changed but sync not run yet/failed?)
    if DEFAULT_SECRET not in key_map:
        key_map[DEFAULT_SECRET] = 1

    for key, uid in key_map.items():
        expected_sign = sign_data(d, key)
        if hmac.compare_digest(expected_sign, s):
            matched_key = key
            matched_user_id = uid
            break

    if not matched_key:
        raise HTTPException(status_code=403, detail="Integrity Check Failed (Invalid Signature)")

    key_prefix = matched_key[:5] if len(matched_key) >= 5 else matched_key
    logging.info(f"Access granted using key starting with: {key_prefix}")

    # LOG STATS
    if matched_user_id:
        log_action(matched_user_id, 'view_stateless')

    try:
        html_content = decompress_payload(d)
        return html_content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decoding error: {str(e)}")

# Admin / Legacy routes
@app.get("/p/{slug}", response_class=HTMLResponse)
async def run_persistent_app_admin(slug: str):
    app_data = get_app(slug, user_id=1)
    if not app_data:
        raise HTTPException(status_code=404, detail="App not found")

    # LOG STATS
    log_action(1, 'view_persistent', slug=slug)

    return HTMLResponse(content=app_data['html_content'])

# User routes
@app.get("/p{user_id}/{slug}", response_class=HTMLResponse)
async def run_persistent_app_user(user_id: int, slug: str):
    app_data = get_app(slug, user_id=user_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="App not found")

    # LOG STATS
    log_action(user_id, 'view_persistent', slug=slug)

    return HTMLResponse(content=app_data['html_content'])

# --- ADMIN PANEL ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

class GenerateRequest(BaseModel):
    domain: Optional[str] = None
    key: str
    html: str
    compress: bool = False

@app.post("/api/generate")
async def generate_api(req: GenerateRequest):
    user = get_current_user_by_key(req.key)

    html_to_process = req.html
    if req.compress:
        html_to_process = minify_html(html_to_process)

    payload = compress_payload(html_to_process)
    signature = sign_data(payload, req.key)

    domain = req.domain if req.domain else DEFAULT_DOMAIN
    domain = domain.rstrip('/')

    full_url = f"{domain}/?d={payload}&s={signature}"

    # LOG STATS
    log_action(user['id'], 'generate')

    return {"url": full_url}

# --- PERSISTENT APPS API ---

class SaveAppRequest(BaseModel):
    key: str
    slug: str
    html: str
    owner_id: Optional[int] = None # Support saving for other users (Admin only)

class DeleteAppRequest(BaseModel):
    key: str
    owner_id: Optional[int] = None # Support deleting for other users (Admin only)

@app.post("/api/apps")
async def save_app_api(req: SaveAppRequest):
    user = get_current_user_by_key(req.key)

    target_user_id = user['id']
    if req.owner_id is not None:
        if user['id'] != 1:
            raise HTTPException(status_code=403, detail="Only Admin can save to other users")
        target_user_id = req.owner_id

    if not req.slug.strip():
        raise HTTPException(status_code=400, detail="Slug cannot be empty")

    save_app(req.slug.strip(), req.html, user_id=target_user_id)
    return {"status": "ok", "slug": req.slug, "user_id": target_user_id}

@app.get("/api/apps")
async def list_apps_api(key: str):
    user = get_current_user_by_key(key)

    if user['id'] == 1:
        # Admin sees all apps
        apps = list_apps(user_id=None)
    else:
        # User sees only theirs
        apps = list_apps(user_id=user['id'])

    return apps

@app.get("/api/apps/{slug}")
async def get_app_api(slug: str, key: str, target_user_id: Optional[int] = None):
    user = get_current_user_by_key(key)

    uid = user['id']
    if target_user_id is not None:
        if user['id'] != 1 and target_user_id != user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        uid = target_user_id

    app_data = get_app(slug, user_id=uid)
    if not app_data:
        raise HTTPException(status_code=404, detail="App not found")
    return app_data

@app.delete("/api/apps/{slug}")
async def delete_app_api(slug: str, req: DeleteAppRequest, target_user_id: Optional[int] = None):
    user = get_current_user_by_key(req.key)

    uid = user['id']

    # Check body param first (if sent) or query param
    req_target = req.owner_id if req.owner_id is not None else target_user_id

    if req_target is not None:
         if user['id'] != 1 and req_target != user['id']:
             raise HTTPException(status_code=403, detail="Access denied")
         uid = req_target

    delete_app(slug, user_id=uid)
    return {"status": "deleted", "slug": slug}

# --- USER MANAGEMENT API ---

class CreateUserRequest(BaseModel):
    key: str
    comment: Optional[str] = None
    admin_key: str

@app.post("/api/users")
async def create_user_api(req: CreateUserRequest):
    admin = get_current_user_by_key(req.admin_key)
    if admin['id'] != 1:
        raise HTTPException(status_code=403, detail="Only Admin can create users")

    try:
        new_id = create_user(req.key, req.comment)
        return {"id": new_id, "key": req.key}
    except ValueError:
        raise HTTPException(status_code=400, detail="Key already exists")

@app.get("/api/users")
async def list_users_api(key: str):
    user = get_current_user_by_key(key)
    if user['id'] != 1:
        raise HTTPException(status_code=403, detail="Only Admin can list users")

    users = list_users()
    stats = get_users_stats()

    # Merge stats into users
    for u in users:
        uid = u['id']
        if uid in stats:
            u['stats'] = stats[uid]
        else:
            u['stats'] = {'generated': 0, 'view_stateless': 0, 'view_persistent': 0, 'apps_count': 0}

    return users
