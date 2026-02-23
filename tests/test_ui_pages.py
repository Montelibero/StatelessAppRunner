from ui.pages import render_home_page, render_admin_page


def test_render_home_page_contains_core_markers():
    html = render_home_page()
    assert "Stateless App Runner" in html
    assert "bulma.min.css" in html
    assert 'href="/admin"' in html
    assert "View source on GitHub" in html


def test_render_admin_page_contains_core_markers():
    html = render_admin_page()
    assert "Генератор ссылок" in html
    assert "bulma.min.css" in html
    assert 'id="generate-btn"' in html
    assert 'const fullKey = "mini" + uuidPart;' not in html
