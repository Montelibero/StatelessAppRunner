import sqlite3
from datetime import datetime

import db


def test_init_db_recovers_when_legacy_admin_key_taken_by_another_user():
    db_file = db.DB_PATH

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS access_logs")
    c.execute("DROP TABLE IF EXISTS apps")
    c.execute("DROP TABLE IF EXISTS apps_old")
    c.execute("DROP TABLE IF EXISTS users")

    c.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            comment TEXT,
            created_at TIMESTAMP
        )
        """
    )
    c.execute(
        """
        CREATE TABLE apps_old (
            slug TEXT PRIMARY KEY,
            html_content TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )
    now = datetime.utcnow()
    c.execute(
        "INSERT INTO users (id, key, comment, created_at) VALUES (2, ?, ?, ?)",
        ("legacy-admin", "existing user", now),
    )
    c.execute(
        "INSERT INTO apps_old (slug, html_content, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("hello", "<h1>ok</h1>", now, now),
    )
    conn.commit()
    conn.close()

    db.init_db()

    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT id, key FROM users WHERE id = 1")
    admin = c.fetchone()
    c.execute("SELECT slug, user_id FROM apps")
    apps = c.fetchall()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps_old'")
    apps_old_exists = c.fetchone()
    conn.close()

    assert admin is not None
    assert apps == [("hello", 1)]
    assert apps_old_exists is None
