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

DEFAULT_DOMAIN = os.getenv("APP_DOMAIN", "https://mtlminiapps.us")

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

    # 3. Remove CSS comments /* ... */
    # We apply this globally as it's generally safe, or we could target <style>
    # Given the user request, removing them from <style> blocks is safer.
    def process_style(match):
        open_tag = match.group(1)
        content = match.group(2)
        close_tag = match.group(3)
        # Remove /* ... */ comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return open_tag + content + close_tag

    html_content = re.sub(r'(<style[^>]*>)(.*?)(</style>)', process_style, html_content, flags=re.DOTALL | re.IGNORECASE)

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
    html = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Link Generator Pro</title>

    <!-- Подключаем Bulma CSS 1.0 (поддерживает авто-тему) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.0/css/bulma.min.css">

    <!-- Подключаем иконки Phosphor -->
    <script src="https://unpkg.com/@phosphor-icons/web"></script>

    <style>
        /* Небольшие доработки, так как Bulma минималистична */
        .textarea-code {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            min-height: 250px;
        }

        /* Анимации для уведомлений и результатов */
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-in {
            animation: slideIn 0.3s ease-out forwards;
        }

        /* Контейнер для уведомлений (Toasts) */
        #toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        }
        .toast {
            pointer-events: auto;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        /* Стиль для прогресс-бара лимита */
        .limit-progress-wrapper {
            width: 100px;
            height: 6px;
            background-color: var(--bulma-background-weak);
            border-radius: 99px;
            overflow: hidden;
        }
        .limit-progress-bar {
            height: 100%;
            background-color: var(--bulma-link);
            width: 0%;
            transition: width 0.3s, background-color 0.3s;
        }

        /* --- Красивый Toggle Switch --- */
        .toggle-switch {
            position: relative;
            display: inline-flex;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
            position: absolute;
        }
        .slider {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            background-color: var(--bulma-border); /* Цвет выключенного состояния */
            border-radius: 34px;
            transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
            margin-right: 8px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 2px;
            bottom: 2px;
            background-color: var(--bulma-scheme-main); /* Цвет кругляшка */
            border-radius: 50%;
            transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        /* Состояние Checked */
        .toggle-switch input:checked + .slider {
            background-color: var(--bulma-link); /* Цвет включенного (синий) */
        }
        .toggle-switch input:checked + .slider:before {
            transform: translateX(20px);
        }
        /* Ховер эффект для интерактивности */
        .toggle-switch:hover .slider {
            filter: brightness(0.95);
        }
    </style>
</head>
<body>

    <section class="section">
        <div class="container is-max-desktop">

            <div class="box">
                <!-- Header -->
                <div class="level is-mobile mb-5 pb-4" style="border-bottom: 1px solid var(--bulma-border);">
                    <div class="level-left">
                        <div class="level-item">
                            <span class="icon is-large has-text-link">
                                <i class="ph ph-link" style="font-size: 32px;"></i>
                            </span>
                        </div>
                        <div class="level-item">
                            <h1 class="title is-4">Генератор ссылок</h1>
                        </div>
                    </div>
                    <div class="level-right">
                        <span class="tag is-light is-rounded font-monospace">v2.0 Beta</span>
                    </div>
                </div>

                <!-- Form -->
                <div class="block">

                    <!-- Secret Key -->
                    <div class="field">
                        <label class="label">
                            Секретный ключ
                            <span class="icon is-small has-text-grey-light ml-1" title="Должен совпадать с ENV на сервере" style="cursor: help;">
                                <i class="ph ph-question"></i>
                            </span>
                        </label>
                        <div class="control has-icons-left has-icons-right">
                            <input class="input is-medium" type="password" id="key" placeholder="Введите ваш секретный ключ">
                            <span class="icon is-small is-left">
                                <i class="ph ph-key"></i>
                            </span>
                            <span class="icon is-small is-right" style="pointer-events: all; cursor: pointer;" onclick="toggleKeyVisibility()">
                                <i class="ph ph-eye" id="eye-icon"></i>
                            </span>
                        </div>
                    </div>

                    <!-- Code Editor -->
                    <div class="field mt-5">
                        <div class="level is-mobile mb-2">
                            <div class="level-left">
                                <label class="label mb-0">HTML Код приложения</label>
                            </div>
                            <div class="level-right">
                                <!-- Красивый Toggle Switch вместо старого чекбокса -->
                                <label class="toggle-switch">
                                    <input type="checkbox" id="compress">
                                    <span class="slider"></span>
                                    <span class="is-size-7 has-text-weight-medium">Сжимать (Gzip)</span>
                                </label>
                            </div>
                        </div>
                        <div class="control">
                            <textarea class="textarea textarea-code" id="code" placeholder="<!DOCTYPE html>..."></textarea>
                        </div>
                    </div>

                    <!-- Generate Button -->
                    <div class="field mt-6">
                        <div class="control">
                            <button id="generate-btn" class="button is-link is-fullwidth is-medium" onclick="generate()">
                                <span class="icon">
                                    <i class="ph ph-magic-wand"></i>
                                </span>
                                <span>Сгенерировать ссылку</span>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Result Area -->
                <article class="message is-link mt-6 is-hidden animate-slide-in" id="result">
                    <div class="message-header">
                        <p>Готово</p>

                        <!-- Limit Indicator inside Header -->
                        <div class="is-flex is-align-items-center">
                            <span class="is-size-7 mr-2">
                                <span id="len-info">0</span> / 8193 байт
                            </span>
                            <div class="limit-progress-wrapper">
                                <div id="limit-bar" class="limit-progress-bar"></div>
                            </div>
                        </div>
                    </div>
                    <div class="message-body">
                        <div class="field has-addons">
                            <div class="control is-expanded">
                                <div class="box has-background-scheme-main-ter p-3"
                                     style="border: 1px solid var(--bulma-border); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: monospace;">
                                    <span id="link-text" class="is-size-7"></span>
                                </div>
                            </div>
                        </div>

                        <div class="buttons is-right">
                            <a id="link-anchor" href="#" target="_blank" class="button is-small is-outlined is-link">
                                <span class="icon"><i class="ph ph-arrow-square-out"></i></span>
                                <span>Открыть</span>
                            </a>
                            <button class="button is-small is-link" onclick="copyLink()">
                                <span class="icon"><i class="ph ph-copy"></i></span>
                                <span>Копировать</span>
                            </button>
                        </div>
                    </div>
                </article>

            </div>

            <p class="has-text-centered is-size-7 has-text-grey mt-4">
                Powered by MTL Mini Apps
            </p>
        </div>
    </section>

    <!-- Toasts Container -->
    <div id="toast-container"></div>

    <script>
        // Toggle Password Visibility
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

        // Bulma-style Toast Notification
        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');

            // Map types to Bulma colors
            const colorClass = type === 'error' ? 'is-danger' : 'is-success';
            const iconClass = type === 'error' ? 'ph-warning-circle' : 'ph-check-circle';

            toast.className = `notification ${colorClass} toast animate-slide-in is-light`;
            toast.innerHTML = `
                <button class="delete" onclick="this.parentElement.remove()"></button>
                <div class="is-flex is-align-items-center">
                    <span class="icon mr-2"><i class="ph ${iconClass} is-size-5"></i></span>
                    <span class="has-text-weight-medium">${message}</span>
                </div>
            `;

            container.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        async function generate() {
            const btn = document.getElementById('generate-btn');
            const originalBtnContent = btn.innerHTML;

            // Loading State
            btn.disabled = true;
            btn.classList.add('is-loading');

            const key = document.getElementById('key').value;
            const code = document.getElementById('code').value;
            const compress = document.getElementById('compress').checked;

            if (!code) {
                showToast('Пожалуйста, введите HTML код', 'error');
                resetBtn(btn, originalBtnContent);
                return;
            }

            try {
                let data;

                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ key, html: code, compress })
                    });
                    if (!response.ok) throw new Error('API Error');
                    data = await response.json();
                } catch (e) {
                    // Fallback for UI Preview
                    console.warn("API недоступен в превью, используем мок-данные");
                    await new Promise(r => setTimeout(r, 800));
                    if (window.location.hostname.includes('googleusercontent') || location.protocol === 'file:') {
                         showToast('Демо режим: Backend недоступен', 'error');
                         throw new Error("Backend not connected");
                    }
                    throw e;
                }

                updateUI(data.url);
                showToast('Ссылка успешно сгенерирована!');

            } catch (error) {
                console.error(error);
                showToast('Ошибка: ' + error.message, 'error');
            } finally {
                resetBtn(btn, originalBtnContent);
            }
        }

        function updateUI(url) {
            const resultDiv = document.getElementById('result');
            const linkText = document.getElementById('link-text');
            const linkAnchor = document.getElementById('link-anchor');
            const lenInfo = document.getElementById('len-info');
            const limitBar = document.getElementById('limit-bar');

            resultDiv.classList.remove('is-hidden');
            linkText.innerText = url;
            linkAnchor.href = url;
            lenInfo.innerText = url.length;

            // Logic for limit bar
            const limit = 8193;
            const percentage = Math.min((url.length / limit) * 100, 100);
            limitBar.style.width = `${percentage}%`;

            // Colors via Bulma CSS variables or direct styles
            if (percentage > 90) {
                limitBar.style.backgroundColor = 'var(--bulma-danger)';
            } else if (percentage > 70) {
                limitBar.style.backgroundColor = 'var(--bulma-warning)';
            } else {
                limitBar.style.backgroundColor = 'var(--bulma-link)';
            }
        }

        function resetBtn(btn, content) {
            btn.disabled = false;
            btn.classList.remove('is-loading');
            btn.innerHTML = content;
        }

        function copyLink() {
            const text = document.getElementById('link-text').innerText;
            if (!text) return;

            navigator.clipboard.writeText(text).then(() => {
                showToast('Ссылка скопирована');
            }).catch(err => {
                showToast('Не удалось скопировать', 'error');
            });
        }
    </script>
</body>
</html>
    """
    return html

class GenerateRequest(BaseModel):
    domain: Optional[str] = None
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

    domain = req.domain if req.domain else DEFAULT_DOMAIN
    domain = domain.rstrip('/')

    full_url = f"{domain}/?d={payload}&s={signature}"
    return {"url": full_url}
