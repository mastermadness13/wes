from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required

teachers_bp = Blueprint('teachers', __name__)


@teachers_bp.route('/')
@login_required
def list_teachers():
    conn = db.get_db()
    department = request.args.get('department', '')

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

    return render_template('teachers/list.html', teachers=teachers, department=department)


@teachers_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_teacher():
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        subject = request.form['subject']

        conn = db.get_db()
        conn.execute(
            'INSERT INTO teachers (user_id, name, department, subject) VALUES (?, ?, ?, ?)',
            (session['user_id'], name, department, subject)
        )
        conn.commit()
        flash('تم إضافة المدرس', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/create.html')


@teachers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    if not teacher or (teacher['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        subject = request.form['subject']
        conn.execute('UPDATE teachers SET name=?, department=?, subject=? WHERE id=?',
                     (name, department, subject, id))
        conn.commit()
        flash('تم التحديث', 'success')
        return redirect(url_for('teachers.list_teachers'))

    return render_template('teachers/edit.html', teacher=teacher)


@teachers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_teacher(id):
    conn = db.get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    if not teacher or (teacher['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('teachers.list_teachers'))

    conn.execute('DELETE FROM teachers WHERE id = ?', (id,))
    conn.commit()
    flash('تم الحذف', 'success')
    return redirect(url_for('teachers.list_teachers'))
