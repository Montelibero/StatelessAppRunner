import sqlite3
import sys
from pathlib import Path

import pytest

app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

import db  # noqa: E402


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    db_file = d / "test_agent_schema.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_file))
    db.init_db()
    return db_file


def test_agent_tables_are_created_additively(isolated_db):
    conn = sqlite3.connect(isolated_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}

    assert "users" in tables
    assert "apps" in tables
    assert "agents" in tables
    assert "agent_tokens" in tables
    assert "agent_apps" in tables


def test_legacy_tables_still_work(isolated_db):
    uid = db.create_user("mini-agent-schema-check", "schema-check")
    assert uid >= 1

    db.save_app("legacy-safe", "<h1>ok</h1>", user_id=uid)
    app_row = db.get_app("legacy-safe", user_id=uid)
    assert app_row is not None
    assert app_row["slug"] == "legacy-safe"
