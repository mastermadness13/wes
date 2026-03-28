#!/usr/bin/env python3
"""
Migration script to update the timetable table from 'room' column to 'room_id' column.
Run this script once to migrate your existing database.
"""

import sqlite3
import os

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'data.db')

def migrate_timetable():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    try:
        # Add new columns to rooms table
        try:
            conn.execute('ALTER TABLE rooms ADD COLUMN name_ar TEXT')
        except sqlite3.OperationalError:
            pass  # Column might already exist

        try:
            conn.execute('ALTER TABLE rooms ADD COLUMN type TEXT DEFAULT "قاعة"')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute('ALTER TABLE rooms ADD COLUMN status TEXT DEFAULT "متاحة"')
        except sqlite3.OperationalError:
            pass

        # Update existing rooms to have name_ar = name if empty
        conn.execute('UPDATE rooms SET name_ar = name WHERE name_ar IS NULL')

        # Check if rooms table exists and has data
        rooms = conn.execute('SELECT id, name FROM rooms').fetchall()
        if not rooms:
            print("No rooms found. Please add rooms first via the web interface.")
            return

        # Create room name to id mapping
        room_map = {room['name']: room['id'] for room in rooms}

        # Check if timetable has room column
        cursor = conn.execute('PRAGMA table_info(timetable)')
        columns = [col['name'] for col in cursor.fetchall()]
        
        if 'room' in columns and 'room_id' not in columns:
            # Get existing timetable data
            old_timetable = conn.execute('SELECT * FROM timetable').fetchall()

            # Create new timetable table with correct schema
            conn.execute('''
                CREATE TABLE timetable_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    semester INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    course_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    room_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE CASCADE,
                    FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE,
                    UNIQUE(user_id, day, semester, section)
                )
            ''')

            # Migrate data
            for row in old_timetable:
                room_name = row['room']
                room_id = room_map.get(room_name)

                if room_id is None:
                    print(f"Warning: Room '{room_name}' not found in rooms table. Skipping entry ID {row['id']}")
                    continue

                conn.execute('''
                    INSERT INTO timetable_new (id, user_id, day, semester, section, course_id, teacher_id, room_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (row['id'], row['user_id'], row['day'], row['semester'], row['section'],
                      row['course_id'], row['teacher_id'], room_id, row['created_at']))

            # Drop old table and rename new one
            conn.execute('DROP TABLE timetable')
            conn.execute('ALTER TABLE timetable_new RENAME TO timetable')

            # Recreate index
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timetable_user_id ON timetable(user_id)')

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_timetable()