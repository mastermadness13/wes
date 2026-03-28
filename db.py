import sqlite3
from flask import g
from config import Config

DATABASE = Config.DATABASE

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
    return db

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    with open('schema.sql', mode='r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def create_default_users():
    db = sqlite3.connect(DATABASE)
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
            label = 'القسم العام' if username == 'superadmin' else 'القسم الافتراضي'
            db.execute('INSERT INTO users (username, password, role, label) VALUES (?, ?, ?, ?)',
                       (username, password, role, label))
    db.commit()
    db.close()
