from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
import db

from routes import login_required, super_admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/')
@login_required
@super_admin_required
def list_users():
    conn = db.get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    return render_template('users/list.html', users=users)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        label = request.form['label']

        conn = db.get_db()
        try:
            conn.execute(
                'INSERT INTO users (username, password, role, label) VALUES (?, ?, ?, ?)',
                (username, generate_password_hash(password), role, label)
            )
            conn.commit()
            flash('تم إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            flash('حدث خطأ أثناء إضافة المستخدم: {}'.format(str(e)), 'danger')

    return render_template('users/create.html')


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_user(user_id):
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        label = request.form['label']

        conn.execute('UPDATE users SET username=?, role=?, label=? WHERE id=?',
                     (username, role, label, user_id))
        conn.commit()
        flash('تم تحديث بيانات المستخدم', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/edit.html', user=user)


@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_user(user_id):
    conn = db.get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    flash('تم حذف المستخدم', 'success')
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/change_password', methods=['GET', 'POST'])
@login_required
@super_admin_required
def change_password(user_id):
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        password = request.form['password']
        conn.execute('UPDATE users SET password = ? WHERE id = ?',
                     (generate_password_hash(password), user_id))
        conn.commit()
        flash('تم تغيير كلمة المرور', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/change_password.html', user=user)
