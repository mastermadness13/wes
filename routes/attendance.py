from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
@login_required
def list_attendance():
    conn = db.get_db()
    student_id = request.args.get('student_id', '')

    sql = 'SELECT a.*, s.name as student_name FROM attendance a JOIN students s ON a.student_id = s.id WHERE a.user_id = ?'
    params = [session['user_id']]
    if session.get('role') == 'super_admin':
        sql = 'SELECT a.*, s.name as student_name FROM attendance a JOIN students s ON a.student_id = s.id WHERE 1=1'
        params = []

    if student_id:
        sql += ' AND a.student_id = ?'
        params.append(student_id)

    records = conn.execute(sql, params).fetchall()
    students = conn.execute('SELECT * FROM students WHERE user_id = ?' if session.get('role')!='super_admin' else 'SELECT * FROM students',
                             (session['user_id'],) if session.get('role')!='super_admin' else ()).fetchall()
    return render_template('attendance/list.html', records=records, students=students, student_id=student_id)


@attendance_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_attendance():
    conn = db.get_db()
    students = conn.execute('SELECT * FROM students WHERE user_id = ?' if session.get('role')!='super_admin' else 'SELECT * FROM students',
                             (session['user_id'],) if session.get('role')!='super_admin' else ()).fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        date = request.form['date']
        status = request.form['status']
        note = request.form.get('note', '')

        conn.execute('INSERT INTO attendance (user_id, student_id, date, status, note) VALUES (?, ?, ?, ?, ?)',
                     (session['user_id'], student_id, date, status, note))
        conn.commit()
        flash('تم تسجيل الحضور', 'success')
        return redirect(url_for('attendance.list_attendance'))

    return render_template('attendance/create.html', students=students)


@attendance_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_attendance(id):
    conn = db.get_db()
    record = conn.execute('SELECT * FROM attendance WHERE id = ?', (id,)).fetchone()
    if not record or (record['user_id'] != session['user_id'] and session['role'] != 'super_admin'):
        flash('غير مسموح', 'danger')
        return redirect(url_for('attendance.list_attendance'))

    conn.execute('DELETE FROM attendance WHERE id = ?', (id,))
    conn.commit()
    flash('تم الحذف', 'success')
    return redirect(url_for('attendance.list_attendance'))
