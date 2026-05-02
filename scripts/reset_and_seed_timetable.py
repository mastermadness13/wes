#!/usr/bin/env python3
"""
Reset the `timetable` table and generate department-based test data.

Usage: python scripts/reset_and_seed_timetable.py
"""
import random
import sqlite3
import os
import sys
from collections import defaultdict

# Ensure project root is on sys.path so imports work when executed from scripts/
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import Config

DB = Config.DATABASE
DAY_NAMES = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']


def configure(conn):
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = MEMORY')


def fetch_periods(conn):
    rows = conn.execute('SELECT code, label, start_time, end_time, is_enabled FROM period_settings WHERE is_enabled = 1 ORDER BY sort_order').fetchall()
    return [dict(r) for r in rows]


def main():
    conn = sqlite3.connect(DB)
    configure(conn)
    cur = conn.cursor()

    # Safety: begin transaction
    print('Connecting to DB:', DB)
    try:
        cur.execute('BEGIN IMMEDIATE')

        # Task 1: Delete all timetable rows
        total_before = cur.execute('SELECT COUNT(*) AS c FROM timetable').fetchone()['c']
        deleted = cur.execute('DELETE FROM timetable').rowcount
        # If rowcount is -1, fall back to computing from total_before
        if deleted == -1:
            deleted = total_before
        print(f'Deleted timetable rows: {deleted}')

        # Gather source data
        departments = [dict(r) for r in cur.execute('SELECT id, name FROM departments').fetchall()]
        courses = [dict(r) for r in cur.execute('SELECT id, name, department, year FROM courses').fetchall()]
        teachers = [dict(r) for r in cur.execute('SELECT id, name, department FROM teachers').fetchall()]
        rooms = [dict(r) for r in cur.execute('SELECT id, name, name_ar FROM rooms').fetchall()]
        periods = fetch_periods(conn)

        # Map courses by department
        courses_by_dept = defaultdict(list)
        for c in courses:
            courses_by_dept[(c['department'] or '').strip()].append(c)

        teachers_by_dept = defaultdict(list)
        for t in teachers:
            teachers_by_dept[(t['department'] or '').strip()].append(t)

        # Owner for seeded rows: pick a super_admin or first user
        row = cur.execute("SELECT id FROM users WHERE role = 'super_admin' ORDER BY id LIMIT 1").fetchone()
        owner_user_id = row['id'] if row else 1

        inserted_by_dept = {}
        skipped_conflicts = 0

        for dept in departments:
            dname = (dept['name'] or '').strip()
            dept_courses = courses_by_dept.get(dname, [])
            dept_teachers = teachers_by_dept.get(dname, [])
            if not dept_courses:
                # skip departments with no courses
                print(f'Skipping {dname}: no courses')
                inserted_by_dept[dname] = 0
                continue

            # Ensure we have a distinct owner/user per department to avoid UNIQUE(user_id, day, semester, section)
            owner_row = cur.execute(
                'SELECT id FROM users WHERE role = ? AND department_id = ? LIMIT 1',
                ('admin', dept['id'])
            ).fetchone()
            if owner_row:
                dept_owner_id = owner_row['id']
            else:
                # create a lightweight admin user for this department
                uname = f'seed_admin_dept_{dept["id"]}'
                cur.execute(
                    'INSERT INTO users (username, password, role, label, department_id) VALUES (?, ?, ?, ?, ?)',
                    (uname, 'seed', 'admin', dname, dept['id'])
                )
                dept_owner_id = cur.lastrowid

            # Choose number of periods per day (bounded by available period templates)
            max_periods_available = len(periods)
            # Prefer 5-8 periods per day, but fall back to available count
            min_choice = min(5, max_periods_available)
            max_choice = min(8, max_periods_available)
            if min_choice > max_choice:
                periods_per_day = max_choice
            else:
                periods_per_day = random.randint(min_choice, max_choice)
            chosen_periods = periods[:periods_per_day]

            count_inserted = 0

            # Track occupancy: (day, semester, period_code) -> {teachers, rooms}
            occupancy = defaultdict(lambda: {'teachers': set(), 'rooms': set()})

            for semester in range(1, 5):
                for day in DAY_NAMES:
                    # shuffle course order for variety
                    course_pool = dept_courses.copy()
                    random.shuffle(course_pool)

                    for period in chosen_periods:
                        slot_key = (day, semester, period['code'])

                        # pick a course that is not already in this slot (department-level)
                        course = None
                        for c in course_pool:
                            # simple heuristic: allow reuse across different days/semesters
                            course = c
                            break
                        if not course:
                            skipped_conflicts += 1
                            continue

                        # pick teacher from dept teachers, fallback to any teacher
                        teacher = None
                        for t in (dept_teachers or teachers):
                            if t['id'] not in occupancy[slot_key]['teachers']:
                                teacher = t
                                break
                        if not teacher:
                            skipped_conflicts += 1
                            continue

                        # pick room not used in this slot
                        room = None
                        for r in rooms:
                            if r['id'] not in occupancy[slot_key]['rooms']:
                                room = r
                                break
                        if not room:
                            skipped_conflicts += 1
                            continue

                        # insert row
                        cur.execute(
                            '''
                            INSERT INTO timetable (user_id, day, semester, section, course_id, teacher_id, room_id, start_time, end_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                dept_owner_id,
                                day,
                                semester,
                                period['code'],
                                course['id'],
                                teacher['id'],
                                room['id'],
                                period['start_time'],
                                period['end_time'],
                            ),
                        )
                        count_inserted += 1
                        occupancy[slot_key]['teachers'].add(teacher['id'])
                        occupancy[slot_key]['rooms'].add(room['id'])

            inserted_by_dept[dname] = count_inserted

        conn.commit()

        # Output summary
        print('\nInsertion summary per department:')
        total_inserted = 0
        for d, cnt in inserted_by_dept.items():
            print(f'  {d}: {cnt} rows')
            total_inserted += cnt

        print(f'\nTotal inserted: {total_inserted}')
        print(f'Skipped slots due to constraints: {skipped_conflicts}')

        print('\nSample 10 timetable entries:')
        sample = cur.execute(
            '''SELECT t.id, t.day, t.semester, t.section, c.name as course, c.department as dept, te.name as teacher, r.name_ar as room, t.start_time, t.end_time
               FROM timetable t
               JOIN courses c ON c.id = t.course_id
               JOIN teachers te ON te.id = t.teacher_id
               JOIN rooms r ON r.id = t.room_id
               ORDER BY t.id LIMIT 10'''
        ).fetchall()
        for row in sample:
            print(dict(row))

        # Optional debug grouping
        print('\nDebug: counts by department, day, semester')
        debug_rows = cur.execute(
            '''SELECT c.department as department, t.day, t.semester, COUNT(*) as cnt
               FROM timetable t
               JOIN courses c ON c.id = t.course_id
               GROUP BY c.department, t.day, t.semester
               ORDER BY c.department, t.day, t.semester'''
        ).fetchall()
        for r in debug_rows:
            print(dict(r))

    except Exception as e:
        conn.rollback()
        print('ERROR:', e)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
