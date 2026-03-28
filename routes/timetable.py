from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required


def build_timetable(rows):
    timetable = {}
    for row in rows:
        day = row['day']
        semester = row['semester']
        section = row['section']

        timetable.setdefault(day, {})
        timetable[day].setdefault(semester, {})
        timetable[day][semester][section] = row
    return timetable


timetable_bp = Blueprint('timetable', __name__)


@timetable_bp.route('/')
@login_required
def list_timetable():
    conn = db.get_db()
    selected_department = request.args.get('department_id', '')
    selected_user_id = request.args.get('user_id', '')
    selected_semesters = request.args.getlist('semester')  # can be multiple

    # normalize semesters
    selected_semesters = [int(s) for s in selected_semesters if str(s).isdigit()]

    # default semesters for display: 2
    if not selected_semesters:
        selected_semesters = [2]

    semesters = sorted(set(selected_semesters))

    # Standard academic days: السبت إلى الخميس (6 أيام)
    days = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
    sections = ['A', 'B']
    days_arabic = {
        'السبت': 'السبت',
        'الأحد': 'الأحد',
        'الاثنين': 'الاثنين',
        'الثلاثاء': 'الثلاثاء',
        'الأربعاء': 'الأربعاء',
        'الخميس': 'الخميس'
    }

    sql = 'SELECT t.*, c.name AS course_name, te.name AS teacher_name, r.name AS room_name FROM timetable t JOIN courses c ON t.course_id=c.id JOIN teachers te ON t.teacher_id=te.id JOIN rooms r ON t.room_id=r.id'
    params = []
    where_clauses = []

    if session.get('role') != 'super_admin':
        where_clauses.append('t.user_id = ?')
        params.append(session['user_id'])
    elif selected_user_id:
        where_clauses.append('t.user_id = ?')
        params.append(selected_user_id)

    if selected_department:
        where_clauses.append('c.department = ?')
        params.append(selected_department)

    if semesters:
        placeholders = ','.join('?' for _ in semesters)
        where_clauses.append(f't.semester IN ({placeholders})')
        params.extend(semesters)

    if where_clauses:
        sql += ' WHERE ' + ' AND '.join(where_clauses)

    timetable_rows = conn.execute(sql, params).fetchall()
    timetable = build_timetable(timetable_rows)

    department_rows = conn.execute(
        'SELECT DISTINCT department FROM courses WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT DISTINCT department FROM courses',
        (session['user_id'],) if session.get('role') != 'super_admin' else ()
    ).fetchall()
    departments = [{'id': d['department'], 'name': d['department']} for d in department_rows]

    courses = conn.execute('SELECT * FROM courses WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM courses',
                           (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()
    teachers = conn.execute('SELECT * FROM teachers WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM teachers',
                            (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()

    # Get rooms based on role
    if session.get('role') == 'super_admin':
        rooms = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    else:
        rooms = conn.execute('SELECT * FROM rooms WHERE status = "متاحة" ORDER BY name').fetchall()

    users = []
    if session.get('role') == 'super_admin':
        users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    return render_template('timetable/list.html',
                           timetable=timetable,
                           courses=courses,
                           teachers=teachers,
                           rooms=rooms,
                           selected_department_id=selected_department,
                           selected_user_id=selected_user_id,
                           selected_semesters=selected_semesters,
                           departments=departments,
                           users=users,
                           semesters=semesters,
                           days=days,
                           sections=sections,
                           days_arabic=days_arabic)


@timetable_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_timetable():
    conn = db.get_db()
    courses = conn.execute('SELECT * FROM courses WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM courses',
                           (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()
    teachers = conn.execute('SELECT * FROM teachers WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM teachers',
                            (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()

    # Get rooms based on role
    if session.get('role') == 'super_admin':
        rooms = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    else:
        rooms = conn.execute('SELECT * FROM rooms WHERE status = "متاحة" ORDER BY name').fetchall()

    if request.method == 'POST':
        day = request.form['day']
        semester = int(request.form['semester'])
        section = request.form['section']
        course_id = int(request.form['course_id'])
        teacher_id = int(request.form['teacher_id'])
        room_id = int(request.form['room_id'])
        user_id = int(request.form.get('user_id', session['user_id']))

        # Check room status
        room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
        if not room:
            flash('القاعة غير موجودة', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        if room['status'] == 'غير متاحة':
            flash('القاعة غير متاحة حالياً', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        if room['status'] == 'مقفلة' and session.get('role') != 'super_admin':
            flash('القاعة مقفلة ولا يمكن استخدامها', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        existing = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND section = ?',
                                (user_id, day, semester, section)).fetchone()
        if existing:
            flash('لا يمكن تكرار نفس اليوم/الفصل/الشعبة', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        room_conflict = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND room_id = ?',
                                     (user_id, day, semester, room_id)).fetchone()
        if room_conflict:
            flash('القاعة محجوزة في نفس الفترة. اختر قاعة أخرى.', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        teacher_conflict = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND teacher_id = ?',
                                        (user_id, day, semester, teacher_id)).fetchone()
        if teacher_conflict:
            flash('المدرس مشغول في نفس الفترة. اختر مدرسًا آخر.', 'danger')
            return redirect(url_for('timetable.create_timetable'))

        conn.execute('INSERT INTO timetable (user_id, day, semester, section, course_id, teacher_id, room_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (user_id, day, semester, section, course_id, teacher_id, room_id))
        conn.commit()
        flash('تم إضافة الجدول', 'success')
        return redirect(url_for('timetable.list_timetable'))

    courses = conn.execute('SELECT * FROM courses WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM courses',
                           (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()
    teachers = conn.execute('SELECT * FROM teachers WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM teachers',
                            (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()

    # Get rooms based on role
    if session.get('role') == 'super_admin':
        rooms = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    else:
        rooms = conn.execute('SELECT * FROM rooms WHERE status = "متاحة" ORDER BY name').fetchall()

    users = []
    if session.get('role') == 'super_admin':
        users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    return render_template('timetable/create.html', courses=courses, teachers=teachers, rooms=rooms, users=users)


@timetable_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_timetable(id):
    conn = db.get_db()
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (id,)).fetchone()
    if not entry or (entry['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('timetable.list_timetable'))

    courses = conn.execute('SELECT * FROM courses WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM courses',
                           (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()
    teachers = conn.execute('SELECT * FROM teachers WHERE user_id = ?' if session.get('role') != 'super_admin' else 'SELECT * FROM teachers',
                            (session['user_id'],) if session.get('role') != 'super_admin' else ()).fetchall()

    # Get rooms based on role
    if session.get('role') == 'super_admin':
        rooms = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    else:
        rooms = conn.execute('SELECT * FROM rooms WHERE status = "متاحة" ORDER BY name').fetchall()

    if request.method == 'POST':
        day = request.form['day']
        semester = int(request.form['semester'])
        section = request.form['section']
        course_id = int(request.form['course_id'])
        teacher_id = int(request.form['teacher_id'])
        room_id = int(request.form['room_id'])
        user_id = int(request.form.get('user_id', entry['user_id']))

        # Check room status
        room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
        if not room:
            flash('القاعة غير موجودة', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        if room['status'] == 'غير متاحة':
            flash('القاعة غير متاحة حالياً', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        if room['status'] == 'مقفلة' and session.get('role') != 'super_admin':
            flash('القاعة مقفلة ولا يمكن استخدامها', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        existing = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND section = ? AND id != ?',
                                (user_id, day, semester, section, id)).fetchone()
        if existing:
            flash('لا يمكن تكرار نفس اليوم/الفصل/الشعبة', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        room_conflict = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND room_id = ? AND id != ?',
                                     (user_id, day, semester, room_id, id)).fetchone()
        if room_conflict:
            flash('القاعة محجوزة في نفس الفترة. اختر قاعة أخرى.', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        teacher_conflict = conn.execute('SELECT * FROM timetable WHERE user_id = ? AND day = ? AND semester = ? AND teacher_id = ? AND id != ?',
                                        (user_id, day, semester, teacher_id, id)).fetchone()
        if teacher_conflict:
            flash('المدرس مشغول في نفس الفترة. اختر مدرسًا آخر.', 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        conn.execute('UPDATE timetable SET user_id=?, day=?, semester=?, section=?, course_id=?, teacher_id=?, room_id=? WHERE id=?',
                     (user_id, day, semester, section, course_id, teacher_id, room_id, id))
        conn.commit()
        flash('تم تحديث الجدول', 'success')
        return redirect(url_for('timetable.list_timetable'))

    users = []
    if session.get('role') == 'super_admin':
        users = conn.execute('SELECT id, username FROM users ORDER BY username').fetchall()

    return render_template('timetable/edit.html', entry=entry, courses=courses, teachers=teachers, rooms=rooms, users=users)


@timetable_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_timetable(id):
    conn = db.get_db()
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (id,)).fetchone()
    if not entry or (entry['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('timetable.list_timetable'))

    conn.execute('DELETE FROM timetable WHERE id = ?', (id,))
    conn.commit()
    flash('تم حذف المحاضرة', 'success')
    return redirect(url_for('timetable.list_timetable'))
