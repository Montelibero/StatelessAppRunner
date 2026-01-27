import sqlite3
import os
import datetime
import logging
from typing import List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "apps.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable FK support
    conn.execute("PRAGMA foreign_keys = ON;")
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

    # 2. Check if apps table needs migration
    # Check if user_id column exists in apps
    try:
        c.execute("SELECT user_id FROM apps LIMIT 1")
        needs_migration = False
    except sqlite3.OperationalError:
        # If table exists but user_id is missing, it throws error
        # Verify if table actually exists first
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps'")
        if c.fetchone():
            needs_migration = True
        else:
            # Table doesn't exist, create fresh
            needs_migration = False
            _create_new_apps_table(c)

    if needs_migration:
        logging.info("Migrating database to multi-user schema...")
        try:
            conn.execute("BEGIN TRANSACTION;")

            # Disable FKs temporarily for migration
            conn.execute("PRAGMA foreign_keys = OFF;")

            # Ensure Admin User (ID 1) exists for legacy data mapping
            # We insert a placeholder if not exists, though sync_admin_key will likely be called later.
            # But for FK integrity if we were enforcing it, we need it.
            # Since we turned FK off, we are fine for now, but let's be safe.
            now = datetime.datetime.utcnow()
            # We might not know the key yet, so we'll check if ID 1 exists
            c.execute("SELECT id FROM users WHERE id = 1")
            if not c.fetchone():
                # Insert a placeholder admin user. The key will be updated by sync_admin_key later.
                # using a temporary random key or empty string if allowed? Key is unique/not null.
                # We'll rely on the fact that sync_admin_key runs right after init.
                # Or better: We assume migration implies we are upgrading.
                pass

            # Rename old table
            c.execute("ALTER TABLE apps RENAME TO apps_old")

            # Create new table
            _create_new_apps_table(c)

            # Copy data (Assign to User 1)
            c.execute('''
                INSERT INTO apps (slug, user_id, html_content, created_at, updated_at)
                SELECT slug, 1, html_content, created_at, updated_at FROM apps_old
            ''')

            # Drop old table
            c.execute("DROP TABLE apps_old")

            conn.execute("COMMIT;")
            conn.execute("PRAGMA foreign_keys = ON;")
            logging.info("Migration completed successfully.")

        except Exception as e:
            conn.execute("ROLLBACK;")
            logging.error(f"Migration failed: {e}")
            raise e

    conn.commit()
    conn.close()

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

def sync_admin_key(env_key: str):
    """
    Ensures the User with ID 1 exists and has the provided env_key.
    """
    if not env_key:
        return

    conn = get_connection()
    c = conn.cursor()

    # Check User 1
    c.execute("SELECT * FROM users WHERE id = 1")
    admin = c.fetchone()

    now = datetime.datetime.utcnow()

    if admin:
        # Verify key matches
        if admin['key'] != env_key:
            logging.warning("Updating Admin (ID 1) key to match environment variable.")
            c.execute("UPDATE users SET key = ? WHERE id = 1", (env_key,))
    else:
        logging.info("Creating Admin User (ID 1) from environment key.")
        # We need to force ID=1
        try:
            c.execute("INSERT INTO users (id, key, comment, created_at) VALUES (1, ?, 'Admin (System)', ?)", (env_key, now))
        except sqlite3.IntegrityError:
            # Could happen if key already exists for another ID?
            # But we are forcing ID 1. If ID 1 is free but key is taken by ID 2?
            # Ideally we handle this, but for now let's assume clean slate or consistent state.
            logging.error("Failed to insert Admin user. Key might be in use?")

    conn.commit()
    conn.close()

def save_app(slug: str, html_content: str, user_id: int = 1):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.utcnow()

    # Check if exists for this user
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

    conn.commit()
    conn.close()

def get_app(slug: str, user_id: int = 1) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id))
    row = c.fetchone()
    conn.close()
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
    conn.close()
    return [dict(row) for row in rows]

def delete_app(slug: str, user_id: int = 1):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id))
    conn.commit()
    conn.close()

# --- User Management Functions ---

def get_user_by_key(key: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def create_user(key: str, comment: str = None) -> int:
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.utcnow()
    try:
        c.execute("INSERT INTO users (key, comment, created_at) VALUES (?, ?, ?)", (key, comment, now))
        conn.commit()
        new_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Key already exists")
    conn.close()
    return new_id

def list_users() -> List[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
