import sqlite3
import os
import datetime
import logging
import threading
from typing import List, Optional, Tuple, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "apps.db")

_local = threading.local()

def get_connection():
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            # Check if connection is still open
            conn.total_changes
        except (sqlite3.ProgrammingError, sqlite3.OperationalError):
            conn = None

    if conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Enable FK support and WAL mode
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn = conn
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            comment TEXT,
            created_at TIMESTAMP
        )
    ''')

    # 1.5 Recover from a partial migration (apps_old left behind)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps_old'")
    if c.fetchone():
        logging.warning("Detected leftover apps_old table. Attempting recovery...")
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps'")
        if not c.fetchone():
            _create_new_apps_table(c)
        else:
            c.execute("PRAGMA table_info(apps)")
            cols = {row[1] for row in c.fetchall()}
            if "user_id" not in cols:
                # Old schema with apps_old present: rename and recreate cleanly
                c.execute("ALTER TABLE apps RENAME TO apps_legacy")
                _create_new_apps_table(c)

        _ensure_admin_user(c, "Admin (Auto-migrated)")

        c.execute('''
            INSERT OR IGNORE INTO apps (slug, user_id, html_content, created_at, updated_at)
            SELECT slug, 1, html_content, created_at, updated_at FROM apps_old
        ''')
        c.execute("DROP TABLE apps_old")
        conn.commit()

    # 2. Check if apps table needs migration
    try:
        c.execute("SELECT user_id FROM apps LIMIT 1")
        needs_migration = False
    except sqlite3.OperationalError:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps'")
        if c.fetchone():
            needs_migration = True
        else:
            needs_migration = False
            _create_new_apps_table(c)

    if needs_migration:
        logging.info("Migrating database to multi-user schema...")
        try:
            # In SQLite, PRAGMA foreign_keys should be set before BEGIN.
            conn.execute("PRAGMA foreign_keys = OFF;")
            conn.execute("BEGIN TRANSACTION;")

            # Create placeholder admin to satisfy FK during migration.
            # sync_admin_key() will update the key later.
            _ensure_admin_user(c, "Admin (Auto-migrated)")

            c.execute("ALTER TABLE apps RENAME TO apps_old")
            _create_new_apps_table(c)

            c.execute('''
                INSERT INTO apps (slug, user_id, html_content, created_at, updated_at)
                SELECT slug, 1, html_content, created_at, updated_at FROM apps_old
            ''')

            c.execute("DROP TABLE apps_old")
            conn.execute("COMMIT;")
            logging.info("Migration completed successfully.")

        except Exception as e:
            conn.execute("ROLLBACK;")
            logging.error(f"Migration failed: {e}")
            raise e
        finally:
            conn.execute("PRAGMA foreign_keys = ON;")

    # 3. Create access_logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            slug TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()

def _create_new_apps_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apps (
            slug TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            html_content TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (slug, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')


def _ensure_admin_user(cursor, comment: str):
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if cursor.fetchone():
        return

    now = datetime.datetime.utcnow()
    key = "legacy-admin"
    suffix = 0
    while True:
        cursor.execute("SELECT id FROM users WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row or row[0] == 1:
            break
        suffix += 1
        key = f"legacy-admin-{suffix}"

    cursor.execute(
        "INSERT INTO users (id, key, comment, created_at) VALUES (1, ?, ?, ?)",
        (key, comment, now),
    )

def sync_admin_key(env_key: str):
    if not env_key:
        return

    conn = get_connection()
    now = datetime.datetime.utcnow()

    with conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = 1")
        admin = c.fetchone()

        if admin:
            if admin['key'] != env_key:
                logging.warning("Updating Admin (ID 1) key to match environment variable.")
                c.execute("UPDATE users SET key = ? WHERE id = 1", (env_key,))
        else:
            logging.info("Creating Admin User (ID 1) from environment key.")
            try:
                c.execute("INSERT INTO users (id, key, comment, created_at) VALUES (1, ?, 'Admin (System)', ?)", (env_key, now))
            except sqlite3.IntegrityError:
                logging.error("Failed to insert Admin user. Key might be in use?")

def save_app(slug: str, html_content: str, user_id: int = 1):
    conn = get_connection()
    now = datetime.datetime.utcnow()

    with conn:
        c = conn.cursor()
        c.execute("SELECT slug FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id))
        exists = c.fetchone()

        if exists:
            c.execute('''
                UPDATE apps SET html_content = ?, updated_at = ? WHERE slug = ? AND user_id = ?
            ''', (html_content, now, slug, user_id))
        else:
            c.execute('''
                INSERT INTO apps (slug, user_id, html_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (slug, user_id, html_content, now, now))

def get_app(slug: str, user_id: int = 1) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id))
    row = c.fetchone()
    if row:
        return dict(row)
    return None

def list_apps(user_id: Optional[int] = None) -> List[dict]:
    conn = get_connection()
    c = conn.cursor()

    if user_id is not None:
        c.execute("SELECT slug, updated_at, user_id FROM apps WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
    else:
        c.execute("SELECT slug, updated_at, user_id FROM apps ORDER BY updated_at DESC")

    rows = c.fetchall()
    return [dict(row) for row in rows]

def delete_app(slug: str, user_id: int = 1):
    conn = get_connection()
    with conn:
        c = conn.cursor()
        c.execute("DELETE FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id))

# --- User Management Functions ---

def get_user_by_key(key: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE key = ?", (key,))
    row = c.fetchone()
    if row:
        return dict(row)
    return None

def create_user(key: str, comment: str = None) -> int:
    conn = get_connection()
    now = datetime.datetime.utcnow()
    try:
        with conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (key, comment, created_at) VALUES (?, ?, ?)", (key, comment, now))
            new_id = c.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Key already exists")
    return new_id

def list_users() -> List[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id ASC")
    rows = c.fetchall()
    return [dict(row) for row in rows]

# --- Stats & Logs ---

def log_action(user_id: int, action: str, slug: Optional[str] = None):
    conn = get_connection()
    now = datetime.datetime.utcnow()
    with conn:
        c = conn.cursor()
        c.execute("INSERT INTO access_logs (user_id, action, slug, timestamp) VALUES (?, ?, ?, ?)",
                  (user_id, action, slug, now))

def get_users_stats() -> Dict[int, dict]:
    """
    Returns statistics per user_id.
    Structure: { user_id: { 'generated': 0, 'view_stateless': 0, 'apps_count': 0, 'view_persistent': 0 } }
    """
    conn = get_connection()
    c = conn.cursor()

    stats = {}

    # 1. Logs aggregation
    c.execute('''
        SELECT user_id, action, COUNT(*) as count
        FROM access_logs
        GROUP BY user_id, action
    ''')
    rows = c.fetchall()

    for row in rows:
        uid = row['user_id']
        action = row['action']
        count = row['count']

        if uid not in stats:
            stats[uid] = {'generated': 0, 'view_stateless': 0, 'view_persistent': 0, 'apps_count': 0}

        if action == 'generate':
            stats[uid]['generated'] = count
        elif action == 'view_stateless':
            stats[uid]['view_stateless'] = count
        elif action == 'view_persistent':
            stats[uid]['view_persistent'] = count

    # 2. Apps count
    c.execute('''
        SELECT user_id, COUNT(*) as count
        FROM apps
        GROUP BY user_id
    ''')
    rows = c.fetchall()
    for row in rows:
        uid = row['user_id']
        count = row['count']
        if uid not in stats:
            stats[uid] = {'generated': 0, 'view_stateless': 0, 'view_persistent': 0, 'apps_count': 0}
        stats[uid]['apps_count'] = count

    return stats
