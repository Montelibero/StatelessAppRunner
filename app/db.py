import sqlite3
import os
import datetime
import logging
import threading
import hashlib
import secrets
from typing import List, Optional, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "apps.db")

_local = threading.local()


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def get_connection():
    conn = getattr(_local, "conn", None)
    conn_path = getattr(_local, "conn_path", None)

    # Reopen connection when DB_PATH changes (used by tests via monkeypatch).
    if conn is not None and conn_path != DB_PATH:
        try:
            conn.close()
        except sqlite3.Error:
            pass
        conn = None

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
        _local.conn_path = DB_PATH
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 1. Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            comment TEXT,
            created_at TIMESTAMP
        )
    """)

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

        c.execute("""
            INSERT OR IGNORE INTO apps (slug, user_id, html_content, created_at, updated_at)
            SELECT slug, 1, html_content, created_at, updated_at FROM apps_old
        """)
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

            c.execute("""
                INSERT INTO apps (slug, user_id, html_content, created_at, updated_at)
                SELECT slug, 1, html_content, created_at, updated_at FROM apps_old
            """)

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            slug TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 4. Agent-first additive tables
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE NOT NULL,
            name TEXT,
            secret_hash TEXT NOT NULL,
            created_at TIMESTAMP,
            last_seen_at TIMESTAMP,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_ref_id INTEGER NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            revoked_at TIMESTAMP,
            FOREIGN KEY (agent_ref_id) REFERENCES agents(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_ref_id INTEGER NOT NULL,
            slug TEXT NOT NULL,
            html_content BLOB NOT NULL,
            content_encoding TEXT NOT NULL DEFAULT 'identity',
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            last_accessed_at TIMESTAMP,
            UNIQUE(agent_ref_id, slug),
            FOREIGN KEY (agent_ref_id) REFERENCES agents(id)
        )
        """
    )

    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_apps_last_accessed ON agent_apps(last_accessed_at)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_apps_owner ON agent_apps(agent_ref_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_tokens_owner ON agent_tokens(agent_ref_id)"
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_ref_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            slug TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (agent_ref_id) REFERENCES agents(id)
        )
        """
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_logs_owner ON agent_access_logs(agent_ref_id)"
    )

    conn.commit()


def _create_new_apps_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
            slug TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            html_content TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (slug, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


def _ensure_admin_user(cursor, comment: str):
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if cursor.fetchone():
        return

    now = _utc_now_iso()
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
    now = _utc_now_iso()

    with conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = 1")
        admin = c.fetchone()

        if admin:
            if admin["key"] != env_key:
                logging.warning(
                    "Updating Admin (ID 1) key to match environment variable."
                )
                c.execute("UPDATE users SET key = ? WHERE id = 1", (env_key,))
        else:
            logging.info("Creating Admin User (ID 1) from environment key.")
            try:
                c.execute(
                    "INSERT INTO users (id, key, comment, created_at) VALUES (1, ?, 'Admin (System)', ?)",
                    (env_key, now),
                )
            except sqlite3.IntegrityError:
                logging.error("Failed to insert Admin user. Key might be in use?")


def save_app(slug: str, html_content: str, user_id: int = 1):
    conn = get_connection()
    now = _utc_now_iso()

    with conn:
        c = conn.cursor()
        c.execute(
            "SELECT slug FROM apps WHERE slug = ? AND user_id = ?", (slug, user_id)
        )
        exists = c.fetchone()

        if exists:
            c.execute(
                """
                UPDATE apps SET html_content = ?, updated_at = ? WHERE slug = ? AND user_id = ?
            """,
                (html_content, now, slug, user_id),
            )
        else:
            c.execute(
                """
                INSERT INTO apps (slug, user_id, html_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (slug, user_id, html_content, now, now),
            )


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
        c.execute(
            """
            SELECT slug, updated_at, user_id, LENGTH(CAST(html_content AS BLOB)) AS html_bytes
            FROM apps
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )
    else:
        c.execute(
            """
            SELECT slug, updated_at, user_id, LENGTH(CAST(html_content AS BLOB)) AS html_bytes
            FROM apps
            ORDER BY updated_at DESC
            """
        )

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


def create_user(key: str, comment: Optional[str] = None) -> int:
    conn = get_connection()
    now = _utc_now_iso()
    try:
        with conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (key, comment, created_at) VALUES (?, ?, ?)",
                (key, comment, now),
            )
            new_id = c.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Key already exists")
    if new_id is None:
        raise RuntimeError("Failed to create user: no row id returned")
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
    now = _utc_now_iso()
    with conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO access_logs (user_id, action, slug, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, action, slug, now),
        )


def get_users_stats() -> Dict[int, dict]:
    """
    Returns statistics per user_id.
    Structure: { user_id: { 'generated': 0, 'view_stateless': 0, 'apps_count': 0, 'view_persistent': 0 } }
    """
    conn = get_connection()
    c = conn.cursor()

    stats = {}

    # 1. Logs aggregation
    c.execute("""
        SELECT user_id, action, COUNT(*) as count
        FROM access_logs
        GROUP BY user_id, action
    """)
    rows = c.fetchall()

    for row in rows:
        uid = row["user_id"]
        action = row["action"]
        count = row["count"]

        if uid not in stats:
            stats[uid] = {
                "generated": 0,
                "view_stateless": 0,
                "view_persistent": 0,
                "apps_count": 0,
            }

        if action == "generate":
            stats[uid]["generated"] = count
        elif action == "view_stateless":
            stats[uid]["view_stateless"] = count
        elif action == "view_persistent":
            stats[uid]["view_persistent"] = count

    # 2. Apps count
    c.execute("""
        SELECT user_id, COUNT(*) as count
        FROM apps
        GROUP BY user_id
    """)
    rows = c.fetchall()
    for row in rows:
        uid = row["user_id"]
        count = row["count"]
        if uid not in stats:
            stats[uid] = {
                "generated": 0,
                "view_stateless": 0,
                "view_persistent": 0,
                "apps_count": 0,
            }
        stats[uid]["apps_count"] = count

    return stats


# --- Agent-first auth and app helpers ---


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_or_get_agent(agent_id: str, secret: str, name: Optional[str] = None) -> dict:
    conn = get_connection()
    now = _utc_now_iso()
    secret_hash = _sha256_hex(secret)

    with conn:
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
        row = c.fetchone()
        if row:
            c.execute(
                """
                UPDATE agents
                SET secret_hash = ?, name = COALESCE(?, name), last_seen_at = ?, is_active = 1
                WHERE id = ?
                """,
                (secret_hash, name, now, row["id"]),
            )
            c.execute("SELECT * FROM agents WHERE id = ?", (row["id"],))
            updated = c.fetchone()
            return dict(updated) if updated else dict(row)

        c.execute(
            """
            INSERT INTO agents (agent_id, name, secret_hash, created_at, last_seen_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (agent_id, name, secret_hash, now, now),
        )
        agent_ref_id = c.lastrowid
        if agent_ref_id is None:
            raise RuntimeError("Failed to create agent")
        c.execute("SELECT * FROM agents WHERE id = ?", (agent_ref_id,))
        created = c.fetchone()
        if not created:
            raise RuntimeError("Failed to load created agent")
        return dict(created)


def get_agent_by_agent_id(agent_id: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE agent_id = ? LIMIT 1", (agent_id,))
    row = c.fetchone()
    return dict(row) if row else None


def get_agent_by_id(agent_ref_id: int) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE id = ? LIMIT 1", (agent_ref_id,))
    row = c.fetchone()
    return dict(row) if row else None


def issue_agent_token(agent_ref_id: int, expires_at: Optional[str] = None) -> str:
    conn = get_connection()
    now = _utc_now_iso()
    token = secrets.token_urlsafe(32)
    token_hash = _sha256_hex(token)

    with conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO agent_tokens (agent_ref_id, token_hash, created_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (agent_ref_id, token_hash, now, expires_at),
        )
    return token


def get_agent_by_token(token: str) -> Optional[dict]:
    token_hash = _sha256_hex(token)
    now = _utc_now_iso()
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT a.*
        FROM agent_tokens t
        JOIN agents a ON a.id = t.agent_ref_id
        WHERE t.token_hash = ?
          AND t.revoked_at IS NULL
          AND (t.expires_at IS NULL OR t.expires_at > ?)
          AND a.is_active = 1
        LIMIT 1
        """,
        (token_hash, now),
    )
    row = c.fetchone()
    return dict(row) if row else None


def save_agent_app(
    agent_ref_id: int,
    slug: str,
    html_content: bytes | str,
    *,
    content_encoding: str = "identity",
) -> None:
    conn = get_connection()
    now = _utc_now_iso()
    payload = html_content
    if isinstance(payload, str):
        payload = payload.encode("utf-8")

    with conn:
        c = conn.cursor()
        c.execute(
            "SELECT id FROM agent_apps WHERE agent_ref_id = ? AND slug = ?",
            (agent_ref_id, slug),
        )
        row = c.fetchone()
        if row:
            c.execute(
                """
                UPDATE agent_apps
                SET html_content = ?, content_encoding = ?, updated_at = ?
                WHERE agent_ref_id = ? AND slug = ?
                """,
                (payload, content_encoding, now, agent_ref_id, slug),
            )
        else:
            c.execute(
                """
                INSERT INTO agent_apps (
                    agent_ref_id, slug, html_content, content_encoding, created_at, updated_at, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (agent_ref_id, slug, payload, content_encoding, now, now, now),
            )


def list_agent_apps(agent_ref_id: int) -> List[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT slug, updated_at, last_accessed_at, content_encoding, LENGTH(CAST(html_content AS BLOB)) AS html_bytes
        FROM agent_apps
        WHERE agent_ref_id = ?
        ORDER BY updated_at DESC
        """,
        (agent_ref_id,),
    )
    return [dict(row) for row in c.fetchall()]


def get_agent_app(agent_ref_id: int, slug: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM agent_apps WHERE agent_ref_id = ? AND slug = ?",
        (agent_ref_id, slug),
    )
    row = c.fetchone()
    return dict(row) if row else None


def get_agent_app_by_agent_id(agent_id: str, slug: str) -> Optional[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT aa.*, a.agent_id
        FROM agent_apps aa
        JOIN agents a ON a.id = aa.agent_ref_id
        WHERE a.agent_id = ? AND aa.slug = ?
        LIMIT 1
        """,
        (agent_id, slug),
    )
    row = c.fetchone()
    return dict(row) if row else None


def touch_agent_app_access(agent_ref_id: int, slug: str) -> None:
    conn = get_connection()
    now = _utc_now_iso()
    with conn:
        c = conn.cursor()
        c.execute(
            "UPDATE agent_apps SET last_accessed_at = ? WHERE agent_ref_id = ? AND slug = ?",
            (now, agent_ref_id, slug),
        )


def delete_agent_app(agent_ref_id: int, slug: str) -> None:
    conn = get_connection()
    with conn:
        c = conn.cursor()
        c.execute(
            "DELETE FROM agent_apps WHERE agent_ref_id = ? AND slug = ?",
            (agent_ref_id, slug),
        )


def set_agent_active(agent_ref_id: int, is_active: bool) -> None:
    conn = get_connection()
    now = _utc_now_iso()
    with conn:
        c = conn.cursor()
        c.execute(
            "UPDATE agents SET is_active = ?, last_seen_at = ? WHERE id = ?",
            (1 if is_active else 0, now, agent_ref_id),
        )


def log_agent_action(
    agent_ref_id: int, action: str, slug: Optional[str] = None
) -> None:
    conn = get_connection()
    now = _utc_now_iso()
    with conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO agent_access_logs (agent_ref_id, action, slug, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (agent_ref_id, action, slug, now),
        )


def list_agents_with_stats() -> List[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT
            a.id,
            a.agent_id,
            a.name,
            a.created_at,
            a.last_seen_at,
            a.is_active,
            COALESCE(apps.apps_count, 0) AS apps_count,
            COALESCE(tokens.tokens_count, 0) AS tokens_count,
            COALESCE(logs.stateless_generated_count, 0) AS stateless_generated_count,
            COALESCE(logs.stateless_view_count, 0) AS stateless_view_count,
            COALESCE(logs.persistent_created_count, 0) AS persistent_created_count
        FROM agents a
        LEFT JOIN (
            SELECT agent_ref_id, COUNT(*) AS apps_count
            FROM agent_apps
            GROUP BY agent_ref_id
        ) apps ON apps.agent_ref_id = a.id
        LEFT JOIN (
            SELECT agent_ref_id, COUNT(*) AS tokens_count
            FROM agent_tokens
            GROUP BY agent_ref_id
        ) tokens ON tokens.agent_ref_id = a.id
        LEFT JOIN (
            SELECT
                agent_ref_id,
                SUM(CASE WHEN action = 'generate_stateless' THEN 1 ELSE 0 END) AS stateless_generated_count,
                SUM(CASE WHEN action = 'view_stateless' THEN 1 ELSE 0 END) AS stateless_view_count,
                SUM(CASE WHEN action = 'create_persistent' THEN 1 ELSE 0 END) AS persistent_created_count
            FROM agent_access_logs
            GROUP BY agent_ref_id
        ) logs ON logs.agent_ref_id = a.id
        ORDER BY a.id ASC
        """
    )
    return [dict(row) for row in c.fetchall()]


def get_agent_persist_usage(agent_ref_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT
            COUNT(*) AS apps_count,
            COALESCE(SUM(LENGTH(CAST(html_content AS BLOB))), 0) AS bytes_total
        FROM agent_apps
        WHERE agent_ref_id = ?
        """,
        (agent_ref_id,),
    )
    row = c.fetchone()
    if not row:
        return {"apps_count": 0, "bytes_total": 0}
    return {
        "apps_count": int(row["apps_count"]),
        "bytes_total": int(row["bytes_total"]),
    }


def count_agent_actions_since(agent_ref_id: int, action: str, since_iso: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM agent_access_logs
        WHERE agent_ref_id = ? AND action = ? AND timestamp >= ?
        """,
        (agent_ref_id, action, since_iso),
    )
    row = c.fetchone()
    return int(row["cnt"]) if row else 0
