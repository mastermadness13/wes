from datetime import datetime


DAY_NAMES = {
    0: 'الاثنين',
    1: 'الثلاثاء',
    2: 'الأربعاء',
    3: 'الخميس',
    4: 'الجمعة',
    5: 'السبت',
    6: 'الأحد',
}


def current_day_name(now=None):
    timestamp = now or datetime.now()
    return DAY_NAMES[timestamp.weekday()]


def build_super_admin_dashboard(conn, current_day):
    users = conn.execute('SELECT * FROM users').fetchall()
    counts = {
        'users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'students': conn.execute('SELECT COUNT(*) FROM students').fetchone()[0],
        'teachers': conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0],
        'courses': conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0],
        'timetable': conn.execute('SELECT COUNT(*) FROM timetable').fetchone()[0],
        'departments': conn.execute('SELECT COUNT(*) FROM departments').fetchone()[0],
        'admins': conn.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0],
    }
    departments = conn.execute('SELECT DISTINCT label as name FROM users WHERE label IS NOT NULL').fetchall()
    admins = conn.execute('SELECT username FROM users WHERE role = "admin"').fetchall()
    today_lectures = conn.execute(
        '''
        SELECT t.*, c.name as course_name, te.name as teacher_name, r.name as room_name
        FROM timetable t
        JOIN courses c ON t.course_id = c.id
        JOIN teachers te ON t.teacher_id = te.id
        LEFT JOIN rooms r ON t.room_id = r.id
        WHERE t.day = ?
        ''',
        (current_day,),
    ).fetchall()
    recent_activity = conn.execute(
        '''
        SELECT c.name as course_name, te.name as teacher_name
        FROM timetable t
        JOIN courses c ON t.course_id = c.id
        JOIN teachers te ON t.teacher_id = te.id
        ORDER BY t.created_at DESC LIMIT 5
        '''
    ).fetchall()
    return {
        'users': users,
        'counts': counts,
        'departments': departments,
        'admins': admins,
        'today_lectures': today_lectures,
        'recent_activity': recent_activity,
    }


def build_department_dashboard(conn, department_name, current_day):
    counts = {
        'students': conn.execute('SELECT COUNT(*) FROM students WHERE department = ?', (department_name,)).fetchone()[0] if department_name else 0,
        'teachers': conn.execute('SELECT COUNT(*) FROM teachers WHERE department = ?', (department_name,)).fetchone()[0] if department_name else 0,
        'courses': conn.execute('SELECT COUNT(*) FROM courses WHERE department = ?', (department_name,)).fetchone()[0] if department_name else 0,
        'timetable': conn.execute(
            '''
            SELECT COUNT(*)
            FROM timetable t
            JOIN courses c ON c.id = t.course_id
            WHERE c.department = ?
            ''',
            (department_name,),
        ).fetchone()[0] if department_name else 0,
    }
    today_lectures = conn.execute(
        '''
        SELECT t.*, c.name as course_name, te.name as teacher_name, r.name as room_name
        FROM timetable t
        JOIN courses c ON t.course_id = c.id
        JOIN teachers te ON t.teacher_id = te.id
        LEFT JOIN rooms r ON t.room_id = r.id
        WHERE c.department = ? AND t.day = ?
        ''',
        (department_name, current_day),
    ).fetchall() if department_name else []
    recent_activity = conn.execute(
        '''
        SELECT c.name as course_name, te.name as teacher_name
        FROM timetable t
        JOIN courses c ON t.course_id = c.id
        JOIN teachers te ON t.teacher_id = te.id
        WHERE c.department = ?
        ORDER BY t.created_at DESC LIMIT 5
        ''',
        (department_name,),
    ).fetchall() if department_name else []
    return {
        'counts': counts,
        'today_lectures': today_lectures,
        'recent_activity': recent_activity,
    }
