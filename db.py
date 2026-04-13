import json
import sqlite3

from flask import g

from config import Config

DATABASE = Config.DATABASE
DEFAULT_PERIODS = [
    ('A', 'الفترة أ', '09:00', '12:00', 1, 1),
    ('B', 'الفترة ب', '12:00', '15:00', 1, 2),
    ('C', 'الفترة ج', '15:00', '18:00', 0, 3),
]


def _get_column_names(conn, table_name):
    rows = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    return {row[1] for row in rows}


def _ensure_periods_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS period_settings (
            code TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_enabled INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL
        )
        """
    )
    rows = conn.execute('SELECT code, label FROM period_settings').fetchall()
    existing_codes = {row[0] for row in rows}
    existing_labels = {row[0]: row[1] for row in rows}

    for code, label, start_time, end_time, is_enabled, sort_order in DEFAULT_PERIODS:
        if code not in existing_codes:
            conn.execute(
                """
                INSERT INTO period_settings (code, label, start_time, end_time, is_enabled, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (code, label, start_time, end_time, is_enabled, sort_order),
            )
        elif existing_labels.get(code) != label:
            conn.execute(
                'UPDATE period_settings SET label = ? WHERE code = ?',
                (label, code),
            )


def _ensure_history_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            actor_user_id INTEGER,
            actor_username TEXT,
            message TEXT,
            old_value TEXT,
            new_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_created_at
        ON history(created_at DESC)
        """
    )


def _serialize_history_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def ensure_schema(conn=None):
    should_close = conn is None
    if conn is None:
        conn = sqlite3.connect(DATABASE)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')

    existing_tables = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    if 'courses' in existing_tables:
        course_columns = _get_column_names(conn, 'courses')
        if 'year' not in course_columns:
            conn.execute('ALTER TABLE courses ADD COLUMN year INTEGER NOT NULL DEFAULT 1')
        if 'notes' not in course_columns:
            conn.execute('ALTER TABLE courses ADD COLUMN notes TEXT')

    if 'history' in existing_tables:
        history_columns = _get_column_names(conn, 'history')
        if 'actor_user_id' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN actor_user_id INTEGER')
        if 'actor_username' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN actor_username TEXT')
        if 'message' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN message TEXT')

    _ensure_periods_table(conn)
    _ensure_history_table(conn)
    conn.commit()

    if should_close:
        conn.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.text_factory = str
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        ensure_schema(db)
    return db


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.text_factory = str
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA encoding = "UTF-8"')
    db.execute('PRAGMA foreign_keys = ON')
    with open('schema.sql', mode='r', encoding='utf-8') as f:
        db.executescript(f.read())
    ensure_schema(db)
    db.commit()
    db.close()


def create_default_users():
    db = sqlite3.connect(DATABASE)
    db.text_factory = str
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    from werkzeug.security import generate_password_hash

    users = [
        ('superadmin', generate_password_hash('admin123')),
        ('admin', generate_password_hash('admin123')),
    ]
    for username, password in users:
        exists = db.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone()
        if not exists:
            role = 'super_admin' if username == 'superadmin' else 'admin'
            label = 'General Department' if username == 'superadmin' else 'Default Department'
            db.execute(
                'INSERT INTO users (username, password, role, label) VALUES (?, ?, ?, ?)',
                (username, password, role, label),
            )
    ensure_schema(db)
    db.commit()
    db.close()


def add_history(
    conn,
    action,
    entity_type,
    entity_id=None,
    actor_user_id=None,
    actor_username=None,
    message=None,
    old_value=None,
    new_value=None,
):
    conn.execute(
        """
        INSERT INTO history (
            action,
            entity_type,
            entity_id,
            actor_user_id,
            actor_username,
            message,
            old_value,
            new_value
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            action,
            entity_type,
            entity_id,
            actor_user_id,
            actor_username,
            message,
            _serialize_history_value(old_value),
            _serialize_history_value(new_value),
        ),
    )
