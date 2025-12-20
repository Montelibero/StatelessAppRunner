
import pytest
import re
from fastapi.testclient import TestClient
from .main import app, minify_html

client = TestClient(app)

def test_minify_html_comments():
    html = """
    <div>
        <!-- This is a comment -->
        <p>Hello</p>
        <!-- Another comment -->
    </div>
    """
    minified = minify_html(html)
    assert "<!--" not in minified
    assert "-->" not in minified
    assert "<p>Hello</p>" in minified

def test_minify_html_js_comments():
    html = """
    <script>
        var x = 1; // This is a variable
        var url = "http://example.com"; // URL check
        var protocolRelative = "//cdn.example.com";
        var strWithSlashes = "path//to//file";
        var escaped = "foo \\" // bar"; // check escaped quote
    </script>
    <script src="//ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    """
    minified = minify_html(html)
    assert "var x = 1;" in minified
    assert "// This is a variable" not in minified
    assert "// check escaped quote" not in minified
    # Ensure http:// is NOT removed
    assert "http://example.com" in minified
    # Ensure protocol-relative URL inside string is preserved
    assert '"//cdn.example.com"' in minified
    # Ensure double slashes inside string are preserved
    assert '"path//to//file"' in minified
    # Ensure src="//..." is preserved
    assert 'src="//ajax.googleapis.com' in minified
    # Ensure content inside escaped quotes is preserved
    assert '"foo \\" // bar"' in minified

def test_minify_css_comments():
    html = """
    <style>
        body {
            background: #fff; /* White background */
            color: #000;
        }
        /* Block comment
           spanning lines */
        .class { width: 100%; }
    </style>
    """
    minified = minify_html(html)
    assert "/* White background */" not in minified
    assert "/* Block comment" not in minified
    assert "background: #fff;" in minified
    assert ".class { width: 100%; }" in minified

def test_minify_html_non_script_content():
    html = """
    <p>Visit http://example.com</p>
    <a href="//example.com">Link</a>
    """
    minified = minify_html(html)
    # These should NOT be touched as they are not in <script>
    assert "Visit http://example.com" in minified
    assert 'href="//example.com"' in minified

def test_minify_html_whitespace():
    html = """
    <div>
        <p>  Hello   World  </p>
    </div>
    """
    minified = minify_html(html)
    # It collapses whitespace to single space
    assert "<div> <p> Hello World </p> </div>" == minified

def test_generate_api_with_compression():
    from .main import VALID_KEYS
    valid_key = list(VALID_KEYS)[0]

    html = """
    <!-- Comment -->
    <div class="test">
        // JS Comment
        Content
    </div>
    """

    # 1. Without compression
    response = client.post("/api/generate", json={
        "domain": "http://test.com",
        "key": valid_key,
        "html": html,
        "compress": False
    })
    assert response.status_code == 200
    url_no_compress = response.json()["url"]

    # 2. With compression
    response_compressed = client.post("/api/generate", json={
        "domain": "http://test.com",
        "key": valid_key,
        "html": html,
        "compress": True
    })
    assert response_compressed.status_code == 200
    url_compressed = response_compressed.json()["url"]

    # The compressed URL should likely be shorter or at least different
    assert len(url_compressed) < len(url_no_compress)
