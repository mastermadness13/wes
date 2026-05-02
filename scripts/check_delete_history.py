#!/usr/bin/env python3
import sqlite3
from config import Config

DB = Config.DATABASE

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print('Recent DELETE history (timetable):')
    for r in cur.execute(
        """
        SELECT id, action, entity_type, entity_id, actor_username, message, created_at
        FROM history
        WHERE action='DELETE' AND entity_type='timetable'
        ORDER BY created_at DESC LIMIT 10
        """
    ).fetchall():
        print(dict(r))

    print('\nRecent timetable rows (last 20):')
    for r in cur.execute(
        """
        SELECT t.id, t.user_id, t.day, t.semester, t.section, c.name as course, c.department as dept
        FROM timetable t
        JOIN courses c ON c.id=t.course_id
        ORDER BY t.id DESC LIMIT 20
        """
    ).fetchall():
        print(dict(r))

    conn.close()


if __name__ == '__main__':
    main()
