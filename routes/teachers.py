from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import courses_timetable_admin_required, current_department_name, current_role, current_user_id, login_required
from routes.access import admin_department_required, department_name_allowed, is_super_admin

teachers_bp = Blueprint('teachers', __name__)


def _get_departments_and_subjects(conn):
    departments = conn.execute('SELECT name FROM departments ORDER BY name').fetchall()
    subjects = conn.execute('SELECT DISTINCT name FROM courses ORDER BY name').fetchall()
    return departments, subjects


def _clean_optional_value(value):
    return (value or '').strip()


def _allowed_departments(conn):
    if is_super_admin():
        return _get_departments_and_subjects(conn)[0]
    return [{'name': current_department_name(conn)}]


@teachers_bp.route('/')
@login_required
@admin_department_required
def list_teachers():
    conn = db.get_db()
    requested_department = request.args.get('department', '')
    department = requested_department if is_super_admin() else (current_department_name(conn) or '')
    _, subjects = _get_departments_and_subjects(conn)
    departments = _allowed_departments(conn)

    if is_super_admin():
        sql = '''
        SELECT t.*, COUNT(DISTINCT tt.course_id) as num_subjects, GROUP_CONCAT(DISTINCT tt.semester) as semesters
        FROM teachers t
        LEFT JOIN timetable tt ON t.id = tt.teacher_id
        WHERE 1=1
        '''
        params = []
        if department:
            sql += ' AND t.department = ?'
            params.append(department)
        sql += ' GROUP BY t.id'
        teachers = conn.execute(sql, params).fetchall()
    else:
        # الأدمن يرى فقط معلمي قسمه
        sql = '''
        SELECT t.*, COUNT(DISTINCT tt.course_id) as num_subjects, GROUP_CONCAT(DISTINCT tt.semester) as semesters
        FROM teachers t
        LEFT JOIN timetable tt ON t.id = tt.teacher_id AND tt.user_id = t.user_id
        WHERE t.department = ?
        GROUP BY t.id
        '''
        params = [current_department_name(conn)]
        teachers = conn.execute(sql, params).fetchall()

    return render_template(
        'teachers/list.html',
        teachers=teachers,
        department=department,
        departments=departments,
        subjects=subjects,
    )


@teachers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@courses_timetable_admin_required
def create_teacher():
    conn = db.get_db()
    _, subjects = _get_departments_and_subjects(conn)
    departments = _allowed_departments(conn)

    if request.method == 'POST':
        name = request.form['name'].strip()
        department = _clean_optional_value(request.form.get('department'))
        subject = _clean_optional_value(request.form.get('subject'))
        if not is_super_admin():
            department = current_department_name(conn) or ''

        valid_departments = {row['name'] for row in departments}
        valid_subjects = {row['name'] for row in subjects}
        if (department and department not in valid_departments) or (subject and subject not in valid_subjects):
            flash('Please select department and subject from the list, or leave them blank for now.', 'danger')
            return render_template('teachers/create.html', departments=departments, subjects=subjects)

        conn.execute(
            'INSERT INTO teachers (user_id, name, department, subject) VALUES (?, ?, ?, ?)',
            (current_user_id(), name, department, subject)
        )
        conn.commit()
        flash('Teacher created successfully.', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/create.html', departments=departments, subjects=subjects)


@teachers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@courses_timetable_admin_required
def edit_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    _, subjects = _get_departments_and_subjects(conn)
    departments = _allowed_departments(conn)

    if not teacher or (not is_super_admin() and not department_name_allowed(conn, teacher['department'])):
        flash('Not allowed.', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        department = _clean_optional_value(request.form.get('department'))
        subject = _clean_optional_value(request.form.get('subject'))
        if not is_super_admin():
            department = current_department_name(conn) or ''

        valid_departments = {row['name'] for row in departments}
        valid_subjects = {row['name'] for row in subjects}
        if (department and department not in valid_departments) or (subject and subject not in valid_subjects):
            flash('Please select department and subject from the list, or leave them blank for now.', 'danger')
            return render_template('teachers/edit.html', teacher=teacher, departments=departments, subjects=subjects)

        conn.execute('UPDATE teachers SET name=?, department=?, subject=? WHERE id=?',
                     (name, department, subject, id))
        conn.commit()
        flash('Teacher updated successfully.', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/edit.html', teacher=teacher, departments=departments, subjects=subjects)


@teachers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@courses_timetable_admin_required
def delete_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    if not teacher or (not is_super_admin() and not department_name_allowed(conn, teacher['department'])):
        flash('Not allowed.', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    conn.execute('DELETE FROM teachers WHERE id = ?', (id,))
    conn.commit()
    flash('Teacher deleted successfully.', 'success')
    return redirect(url_for('teachers.list_teachers'))
