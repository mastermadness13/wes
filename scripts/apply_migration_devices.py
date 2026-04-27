#!/usr/bin/env python3
"""Apply migration to add `devices` column to `rooms` table if missing.

Usage:
  python scripts/apply_migration_devices.py --db path/to/clean_data.db
"""
import argparse
import sqlite3
import os
import sys


def has_column(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def main():
    parser = argparse.ArgumentParser(description='Apply devices column migration')
    parser.add_argument('--db', default='clean_data.db', help='Path to SQLite database file')
    args = parser.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        if has_column(conn, 'rooms', 'devices'):
            print("Column 'devices' already exists on 'rooms'. Nothing to do.")
            return

        print("Adding 'devices' column to 'rooms' table...")
        conn.execute('ALTER TABLE rooms ADD COLUMN devices INTEGER DEFAULT 0')
        conn.commit()
        print("Migration applied: 'devices' column added.")
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
