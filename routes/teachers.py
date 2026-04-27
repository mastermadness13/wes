from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required, super_admin_required

teachers_bp = Blueprint('teachers', __name__)


def _get_departments_and_subjects(conn):
    departments = conn.execute('SELECT name FROM departments ORDER BY name').fetchall()
    subjects = conn.execute('SELECT DISTINCT name FROM courses ORDER BY name').fetchall()
    return departments, subjects


def _clean_optional_value(value):
    return (value or '').strip()


@teachers_bp.route('/')
@login_required
@super_admin_required
def list_teachers():
    conn = db.get_db()
    department = request.args.get('department', '')
    departments, subjects = _get_departments_and_subjects(conn)

    if session.get('role') == 'super_admin':
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
        sql = '''
        SELECT t.*, COUNT(DISTINCT tt.course_id) as num_subjects, GROUP_CONCAT(DISTINCT tt.semester) as semesters
        FROM teachers t
        LEFT JOIN timetable tt ON t.id = tt.teacher_id AND tt.user_id = t.user_id
        WHERE t.user_id = ?
        GROUP BY t.id
        '''
        params = [session['user_id']]
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
@super_admin_required
def create_teacher():
    conn = db.get_db()
    departments, subjects = _get_departments_and_subjects(conn)

    if request.method == 'POST':
        name = request.form['name'].strip()
        department = _clean_optional_value(request.form.get('department'))
        subject = _clean_optional_value(request.form.get('subject'))

        valid_departments = {row['name'] for row in departments}
        valid_subjects = {row['name'] for row in subjects}
        if (department and department not in valid_departments) or (subject and subject not in valid_subjects):
            flash('Please select department and subject from the list, or leave them blank for now.', 'danger')
            return render_template('teachers/create.html', departments=departments, subjects=subjects)

        conn.execute(
            'INSERT INTO teachers (user_id, name, department, subject) VALUES (?, ?, ?, ?)',
            (session['user_id'], name, department, subject)
        )
        conn.commit()
        flash('Teacher created successfully.', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/create.html', departments=departments, subjects=subjects)


@teachers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    departments, subjects = _get_departments_and_subjects(conn)

    if not teacher or (teacher['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('Not allowed.', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        department = _clean_optional_value(request.form.get('department'))
        subject = _clean_optional_value(request.form.get('subject'))

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
@super_admin_required
def delete_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    if not teacher or (teacher['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('Not allowed.', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    conn.execute('DELETE FROM teachers WHERE id = ?', (id,))
    conn.commit()
    flash('Teacher deleted successfully.', 'success')
    return redirect(url_for('teachers.list_teachers'))
