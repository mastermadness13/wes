from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/')
@login_required
def list_courses():
    conn = db.get_db()
    department = request.args.get('department', '')

    if session.get('role') == 'super_admin':
        sql = 'SELECT * FROM courses WHERE 1=1'
        params = []
        if department:
            sql += ' AND department = ?'
            params.append(department)
        courses = conn.execute(sql, params).fetchall()
    else:
        sql = '''
        SELECT c.*, GROUP_CONCAT(DISTINCT te.name) as teachers, GROUP_CONCAT(DISTINCT t.semester) as semesters
        FROM courses c
        LEFT JOIN timetable t ON c.id = t.course_id AND t.user_id = c.user_id
        LEFT JOIN teachers te ON t.teacher_id = te.id
        WHERE c.user_id = ?
        GROUP BY c.id
        '''
        params = [session['user_id']]
        courses = conn.execute(sql, params).fetchall()

    return render_template('courses/list.html', courses=courses, department=department)


@courses_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        department = request.form['department']

        conn = db.get_db()
        conn.execute(
            'INSERT INTO courses (user_id, name, code, department) VALUES (?, ?, ?, ?)',
            (session['user_id'], name, code, department)
        )
        conn.commit()
        flash('تم إضافة المادة', 'success')
        return redirect(url_for('courses.list_courses'))

    return render_template('courses/create.html')


@courses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(id):
    conn = db.get_db()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (id,)).fetchone()
    if not course or (course['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('courses.list_courses'))

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        department = request.form['department']
        conn.execute('UPDATE courses SET name=?, code=?, department=? WHERE id=?',
                     (name, code, department, id))
        conn.commit()
        flash('تم التحديث', 'success')
        return redirect(url_for('courses.list_courses'))

    return render_template('courses/edit.html', course=course)


@courses_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_course(id):
    conn = db.get_db()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (id,)).fetchone()
    if not course or (course['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('courses.list_courses'))

    conn.execute('DELETE FROM courses WHERE id = ?', (id,))
    conn.commit()
    flash('تم الحذف', 'success')
    return redirect(url_for('courses.list_courses'))
