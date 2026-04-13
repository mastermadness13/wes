from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required, super_admin_required

departments_bp = Blueprint('departments', __name__)


@departments_bp.route('/')
@login_required
@super_admin_required
def list_departments():
    conn = db.get_db()
    if session.get('role') == 'super_admin':
        sql = 'SELECT * FROM departments'
        params = ()
    else:
        sql = 'SELECT * FROM departments'
        params = ()

    departments = conn.execute(sql, params).fetchall()
    return render_template('departments/list.html', departments=departments)


@departments_bp.route('/create', methods=['POST'])
@login_required
@super_admin_required
def create_department():
    name = request.form['name']
    semesters = int(request.form['semesters'])
    majors = int(request.form['majors'])

    conn = db.get_db()
    try:
        conn.execute('INSERT INTO departments (name, semesters, majors) VALUES (?, ?, ?)',
                     (name, semesters, majors))
        conn.commit()
        flash('تمت إضافة القسم بنجاح', 'success')
    except Exception as e:
        flash('حدث خطأ أثناء إضافة القسم: {}'.format(e), 'danger')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
@super_admin_required
def edit_department(id):
    name = request.form['name']
    semesters = int(request.form['semesters'])
    majors = int(request.form['majors'])

    conn = db.get_db()
    conn.execute('UPDATE departments SET name=?, semesters=?, majors=? WHERE id=?',
                 (name, semesters, majors, id))
    conn.commit()
    flash('تم تحديث القسم', 'success')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_department(id):
    conn = db.get_db()
    conn.execute('DELETE FROM departments WHERE id = ?', (id,))
    conn.commit()
    flash('تم حذف القسم', 'success')
    return redirect(url_for('departments.list_departments'))
