import os
import zlib
import base64
import hmac
import hashlib
import secrets
import logging
import re
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Stateless App Runner")

# Настройки по умолчанию
DEFAULT_SECRET = os.getenv("SECRET_KEY")
if not DEFAULT_SECRET:
    DEFAULT_SECRET = secrets.token_urlsafe(32)
    logging.warning(f"No SECRET_KEY set. Generated random secret: {DEFAULT_SECRET}")

# Initialize VALID_KEYS with DEFAULT_SECRET
VALID_KEYS = {DEFAULT_SECRET}

# Add keys from SECRET_KEYS environment variable
SECRET_KEYS_ENV = os.getenv("SECRET_KEYS")
if SECRET_KEYS_ENV:
    extra_keys = [k.strip() for k in SECRET_KEYS_ENV.split(",") if k.strip()]
    VALID_KEYS.update(extra_keys)
    logging.info(f"Loaded {len(extra_keys)} additional keys from SECRET_KEYS")

DEFAULT_DOMAIN = os.getenv("APP_DOMAIN", "http://mtlminiapps.us")

# --- ЛОГИКА (Core Logic) ---

def sign_data(data: str, key: str) -> str:
    key_bytes = key.encode('utf-8')
    return hmac.new(key_bytes, data.encode('utf-8'), hashlib.sha256).hexdigest()

def compress_payload(html: str) -> str:
    # 1. Сжимаем
    compressed = zlib.compress(html.encode('utf-8'), level=9)
    # 2. Base64 URL-safe (без padding)
    return base64.urlsafe_b64encode(compressed).decode('utf-8').rstrip('=')

def decompress_payload(payload: str) -> str:
    # Возвращаем padding если нужно
    padding = 4 - (len(payload) % 4)
    if padding != 4:
        payload += '=' * padding

    compressed_data = base64.urlsafe_b64decode(payload)
    return zlib.decompress(compressed_data).decode('utf-8')

def remove_js_comments(text: str) -> str:
    """
    Parses JS content to remove // comments while respecting quotes.
    Handles ', ", and ` quotes.
    """
    out = []
    i = 0
    n = len(text)
    in_quote = None

    while i < n:
        char = text[i]

        # Check for quote start/end
        if in_quote:
            if char == in_quote:
                # Check for escaped quote (count preceding backslashes)
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

        # Check for // comment
        if char == '/' and i + 1 < n and text[i+1] == '/':
            # Found comment, skip until newline
            i += 2
            while i < n and text[i] != '\n':
                i += 1
            # We skip the comment but continue loop (next char is newline or end)
            continue

        out.append(char)
        i += 1

    return "".join(out)

def minify_html(html_content: str) -> str:
    """
    Simple minification:
    1. Remove HTML comments <!-- ... -->
    2. Remove JS comments // ... ONLY inside <script> tags using a parser.
    3. Collapse whitespace
    """
    # 1. Remove HTML comments
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

    # 2. Process <script> tags to remove JS comments
    def process_script(match):
        open_tag = match.group(1)
        content = match.group(2)
        close_tag = match.group(3)
        return open_tag + remove_js_comments(content) + close_tag

    # Match <script...>content</script>
    # Use DOTALL so . matches newlines in content
    # Use IGNORECASE for <SCRIPT>
    html_content = re.sub(r'(<script[^>]*>)(.*?)(</script>)', process_script, html_content, flags=re.DOTALL | re.IGNORECASE)

    # 3. Collapse whitespace (newlines, tabs, multiple spaces -> single space)
    html_content = re.sub(r'\s+', ' ', html_content)

    return html_content.strip()

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def run_app(d: str = None, s: str = None):
    """
    Runner: принимает payload (d) и подпись (s).
    """
    if not d or not s:
        return """
        <html><body><h1>Stateless App Runner</h1>
        <p>Нет данных для запуска. Перейдите в <a href="/admin">/admin</a> для создания ссылки.</p>
        </body></html>
        """

    # 1. Проверяем подпись (Check signature against all valid keys)
    matched_key = None
    for key in VALID_KEYS:
        expected_sign = sign_data(d, key)
        if hmac.compare_digest(expected_sign, s):
            matched_key = key
            break

    if not matched_key:
        # На случай, если ссылка была сгенерирована другим ключом, но мы хотим проверить целостность
        # Здесь мы строго отклоняем, если подпись не совпадает с КЛЮЧОМ СЕРВЕРА
        raise HTTPException(status_code=403, detail="Integrity Check Failed (Invalid Signature)")

    # Log successful access with key prefix
    key_prefix = matched_key[:5] if len(matched_key) >= 5 else matched_key
    logging.info(f"Access granted using key starting with: {key_prefix}")

    try:
        # 2. Декодируем
        html_content = decompress_payload(d)
        return html_content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decoding error: {str(e)}")


# --- ADMIN PANEL ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    # Простая HTML форма прямо внутри кода для удобства
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Link Generator</title>
        <style>
            body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
            .form-group {{ margin-bottom: 1rem; }}
            label {{ display: block; margin-bottom: 0.5rem; font-weight: bold; }}
            input, textarea {{ width: 100%; padding: 0.5rem; box-sizing: border-box; }}
            textarea {{ height: 300px; font-family: monospace; }}
            button {{ padding: 1rem 2rem; background: #007bff; color: white; border: none; cursor: pointer; font-size: 1rem; }}
            button:hover {{ background: #0056b3; }}
            #result {{ margin-top: 2rem; padding: 1rem; background: #f8f9fa; border: 1px solid #ddd; word-break: break-all; display: none; }}
            .hint {{ font-size: 0.8rem; color: #666; }}
        </style>
    </head>
    <body>
        <h1>Генератор ссылок</h1>

        <div class="form-group">
            <label>Домен (Base URL)</label>
            <input type="text" id="domain" value="{DEFAULT_DOMAIN}">
        </div>

        <div class="form-group">
            <label>Секретный ключ (Secret Key)</label>
            <input type="password" id="key" placeholder="Введите ваш секретный ключ">
            <div class="hint">Важно: Ссылка откроется только на сервере, у которого этот ключ совпадает с переменной окружения.</div>
        </div>

        <div class="form-group">
            <label>HTML Код приложения</label>
            <textarea id="code" placeholder="<!DOCTYPE html>..."></textarea>
        </div>

        <div class="form-group">
            <label><input type="checkbox" id="compress"> Сжимать</label>
        </div>

        <button onclick="generate()">Сгенерировать ссылку</button> <span>ограничение в тг 8193</span>

        <div id="result">
            <h3>Ваша ссылка (<span id="len-info">0</span> байт):</h3>
            <a id="link-anchor" href="#" target="_blank">Открыть</a>
            <p id="link-text"></p>
        </div>

        <script>
            async function generate() {{
                const domain = document.getElementById('domain').value.replace(/\\/$/, "");
                const key = document.getElementById('key').value;
                const code = document.getElementById('code').value;
                const compress = document.getElementById('compress').checked;

                if (!code) {{ alert('Введите HTML код'); return; }}

                // Отправляем на сервер для генерации (чтобы zlib был идентичен)
                const response = await fetch('/api/generate', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ domain, key, html: code, compress }})
                }});

                const data = await response.json();

                const resultDiv = document.getElementById('result');
                const linkText = document.getElementById('link-text');
                const linkAnchor = document.getElementById('link-anchor');
                const lenInfo = document.getElementById('len-info');

                resultDiv.style.display = 'block';
                linkText.innerText = data.url;
                linkAnchor.href = data.url;
                lenInfo.innerText = data.url.length;
            }}
        </script>
    </body>
    </html>
    """
    return html

class GenerateRequest(BaseModel):
    domain: str
    key: str
    html: str
    compress: bool = False

@app.post("/api/generate")
async def generate_api(req: GenerateRequest):
    if req.key not in VALID_KEYS:
        raise HTTPException(status_code=403, detail="Invalid Key. You must provide a valid server key.")

    html_to_process = req.html
    if req.compress:
        html_to_process = minify_html(html_to_process)

    payload = compress_payload(html_to_process)
    signature = sign_data(payload, req.key)
    full_url = f"{req.domain}/?d={payload}&s={signature}"
    return {"url": full_url}
