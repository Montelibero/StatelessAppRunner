import base64
import hashlib
import hmac
import re
import zlib


def sign_data(data: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    return hmac.new(key_bytes, data.encode("utf-8"), hashlib.sha256).hexdigest()


def compress_payload(html: str) -> str:
    compressed = zlib.compress(html.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("utf-8").rstrip("=")


def decompress_payload(payload: str) -> str:
    padding = 4 - (len(payload) % 4)
    if padding != 4:
        payload += "=" * padding
    compressed_data = base64.urlsafe_b64decode(payload)
    return zlib.decompress(compressed_data).decode("utf-8")


def remove_js_comments(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    in_quote = None
    while i < n:
        char = text[i]
        if in_quote:
            if char == in_quote:
                j = i - 1
                backslashes = 0
                while j >= 0 and text[j] == "\\":
                    backslashes += 1
                    j -= 1
                if backslashes % 2 == 0:
                    in_quote = None
            out.append(char)
            i += 1
            continue
        if char in ('"', "'", "`"):
            in_quote = char
            out.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(char)
        i += 1
    return "".join(out)


def minify_html(html_content: str) -> str:
    html_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)

    def process_script(match):
        return match.group(1) + remove_js_comments(match.group(2)) + match.group(3)

    html_content = re.sub(
        r"(<script[^>]*>)(.*?)(</script>)",
        process_script,
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    def process_style(match):
        content = re.sub(r"/\*.*?\*/", "", match.group(2), flags=re.DOTALL)
        return match.group(1) + content + match.group(3)

    html_content = re.sub(
        r"(<style[^>]*>)(.*?)(</style>)",
        process_style,
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html_content = re.sub(r"\s+", " ", html_content)
    return html_content.strip()
