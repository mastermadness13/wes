from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required, super_admin_required

students_bp = Blueprint('students', __name__)


@students_bp.route('/')
@login_required
@super_admin_required
def list_students():
    conn = db.get_db()
    department = request.args.get('department', '')
    class_name = request.args.get('class', '')

    sql = 'SELECT * FROM students WHERE user_id = ?'
    params = [session['user_id']]

    if session.get('role') == 'super_admin':
        sql = 'SELECT * FROM students WHERE 1=1'
        params = []

    if department:
        sql += ' AND department = ?'
        params.append(department)
    if class_name:
        sql += ' AND class = ?'
        params.append(class_name)

    students = conn.execute(sql, params).fetchall()
    return render_template('students/list.html', students=students, department=department, class_name=class_name)


@students_bp.route('/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_student():
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        class_name = request.form['class']

        conn = db.get_db()
        conn.execute(
            'INSERT INTO students (user_id, name, department, class) VALUES (?, ?, ?, ?)',
            (session['user_id'], name, department, class_name)
        )
        conn.commit()
        flash('تم إضافة الطالب', 'success')
        return redirect(url_for('students.list_students'))

    return render_template('students/create.html')


@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_student(id):
    conn = db.get_db()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    if not student or (student['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('students.list_students'))

    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        class_name = request.form['class']
        conn.execute(
            'UPDATE students SET name = ?, department = ?, class = ? WHERE id = ?',
            (name, department, class_name, id)
        )
        conn.commit()
        flash('تم التحديث', 'success')
        return redirect(url_for('students.list_students'))

    return render_template('students/edit.html', student=student)


@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_student(id):
    conn = db.get_db()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    if not student or (student['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('students.list_students'))

    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    flash('تم الحذف', 'success')
    return redirect(url_for('students.list_students'))
