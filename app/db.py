import sqlite3
import os
import datetime
from typing import List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "apps.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS apps (
            slug TEXT PRIMARY KEY,
            html_content TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_app(slug: str, html_content: str):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.utcnow()

    # Check if exists
    c.execute("SELECT slug FROM apps WHERE slug = ?", (slug,))
    exists = c.fetchone()

    if exists:
        c.execute('''
            UPDATE apps SET html_content = ?, updated_at = ? WHERE slug = ?
        ''', (html_content, now, slug))
    else:
        c.execute('''
            INSERT INTO apps (slug, html_content, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (slug, html_content, now, now))

    conn.commit()
    conn.close()

def get_app(slug: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM apps WHERE slug = ?", (slug,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def list_apps() -> List[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT slug, updated_at FROM apps ORDER BY updated_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_app(slug: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM apps WHERE slug = ?", (slug,))
    conn.commit()
    conn.close()
