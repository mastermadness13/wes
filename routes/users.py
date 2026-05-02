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
    users = conn.execute(
        '''
        SELECT u.*, d.name AS department_name
        FROM users u
        LEFT JOIN departments d ON d.id = u.department_id
        ORDER BY u.username
        '''
    ).fetchall()
    return render_template('users/list.html', users=users)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_user():
    conn = db.get_db()
    departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
    is_modal = request.values.get('modal') in {'1', 'true', 'True'}
    # Allow optionally prefilling department via query string (?department_id=...)
    selected_department_id = request.args.get('department_id', type=int) or request.values.get('department_id', type=int)
    default_label = None
    if selected_department_id:
        dept = conn.execute('SELECT name FROM departments WHERE id = ?', (selected_department_id,)).fetchone()
        if dept:
            default_label = dept['name']
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form['password']
        role = request.form['role']
        label = request.form['label'].strip()
        department_id = request.form.get('department_id', type=int)

        if not username:
            flash('اسم المستخدم مطلوب.', 'danger')
            return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)

        allowed_roles = {'admin', 'super_admin'}
        if role not in allowed_roles:
            flash('Invalid role selected.', 'danger')
            return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)
        if role == 'admin' and not department_id:
            flash('Admin accounts must be linked to a department.', 'danger')
            return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)
        if role == 'super_admin':
            department_id = None

        # NEW: Robust automatic label generation
        if not label and department_id:
            dept_row = conn.execute('SELECT name FROM departments WHERE id = ?', (department_id,)).fetchone()
            if dept_row:
                label = dept_row['name']
            else:
                label = username

        try:
            conn.execute(
                'INSERT INTO users (username, password, role, label, department_id) VALUES (?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), role, label, department_id)
            )
            conn.commit()
            flash('تم إضافة المستخدم بنجاح', 'success')
            if is_modal:
                return render_template('timetable/modal_success.html', message='تم إضافة المستخدم بنجاح')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            flash('حدث خطأ أثناء إضافة المستخدم: {}'.format(str(e)), 'danger')
            return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)
    # For GET requests (or any path not returning above), render the create form
    return render_template('users/create.html', departments=departments, is_modal=is_modal, hide_nav=is_modal, default_label=default_label, selected_department_id=selected_department_id)


@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # فقط super_admin أو المستخدم نفسه يمكنه التعديل
    if session.get('role') != 'super_admin' and session.get('user_id') != user_id:
        flash('ليس لديك صلاحية تعديل هذا المستخدم.', 'danger')
        return redirect(url_for('auth.dashboard'))
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users.list_users'))

    # جلب جميع الأقسام لعرضها في القائمة المنسدلة
    departments = conn.execute('SELECT * FROM departments').fetchall()

    if request.method == 'POST':
        username = request.form['username'].strip()
        label = request.form['label'].strip()
        if session.get('role') == 'super_admin':
            role = request.form['role']
            department_id = request.form.get('department_id', type=int)
            allowed_roles = {'admin', 'super_admin'}
            if role not in allowed_roles:
                flash('Invalid role selected.', 'danger')
                return render_template('users/edit.html', user=user, departments=departments)
            if user['role'] == 'super_admin' and role != 'super_admin':
                super_admin_count = conn.execute(
                    'SELECT COUNT(*) FROM users WHERE role = "super_admin"'
                ).fetchone()[0]
                if super_admin_count <= 1:
                    flash('Cannot demote the last super admin.', 'danger')
                    return render_template('users/edit.html', user=user, departments=departments)
            if role == 'admin' and not department_id:
                flash('Admin accounts must be linked to a department.', 'danger')
                return render_template('users/edit.html', user=user, departments=departments)
            if role == 'super_admin':
                department_id = None

            # تحديث الاسم الظاهر آلياً عند تركه فارغاً من قبل المشرف العام
            if not label and department_id:
                dept_row = conn.execute('SELECT name FROM departments WHERE id = ?', (department_id,)).fetchone()
                if dept_row:
                    label = dept_row['name']

            conn.execute('UPDATE users SET username=?, role=?, label=?, department_id=? WHERE id=?',
                         (username, role, label, department_id, user_id))
        else:
            # تحديث الاسم الظاهر آلياً للأدمن عند تعديل ملفه الشخصي وتركه فارغاً
            if not label and user['department_id']:
                dept_row = conn.execute('SELECT name FROM departments WHERE id = ?', (user['department_id'],)).fetchone()
                if dept_row:
                    label = dept_row['name']

            # الأدمن يعدل اسم المستخدم والاسم الظاهر فقط
            conn.execute('UPDATE users SET username=?, label=? WHERE id=?',
                         (username, label, user_id))
        conn.commit()
        if session.get('user_id') == user_id:
            refreshed = conn.execute('SELECT username, role, label, department_id FROM users WHERE id = ?', (user_id,)).fetchone()
            if refreshed:
                session['username'] = refreshed['username']
                session['role'] = refreshed['role']
                session['label'] = refreshed['label']
                if refreshed['role'] == 'admin' and refreshed['department_id'] is not None:
                    session['department_id'] = refreshed['department_id']
                else:
                    session.pop('department_id', None)
        flash('تم تحديث بيانات المستخدم', 'success')
        return redirect(url_for('auth.dashboard'))
    return render_template('users/edit.html', user=user, departments=departments)


@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_user(user_id):
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('users.list_users'))
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users.list_users'))
    if user['role'] == 'super_admin':
        super_admin_count = conn.execute(
            'SELECT COUNT(*) FROM users WHERE role = "super_admin"'
        ).fetchone()[0]
        if super_admin_count <= 1:
            flash('Cannot delete the last super admin.', 'danger')
            return redirect(url_for('users.list_users'))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    flash('تم حذف المستخدم', 'success')
    return redirect(url_for('users.list_users'))


@users_bp.route('/<int:user_id>/change_password', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    # فقط super_admin أو المستخدم نفسه يمكنه تغيير كلمة المرور
    if session.get('role') != 'super_admin' and session.get('user_id') != user_id:
        flash('ليس لديك صلاحية تغيير كلمة المرور لهذا المستخدم.', 'danger')
        return redirect(url_for('auth.dashboard'))
    conn = db.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('المستخدم غير موجود', 'danger')
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        password = request.form['password']
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('users/change_password.html', user=user)
        conn.execute('UPDATE users SET password = ? WHERE id = ?',
                     (generate_password_hash(password), user_id))
        conn.commit()
        flash('تم تغيير كلمة المرور', 'success')
        return redirect(url_for('users.list_users'))

    return render_template('users/change_password.html', user=user)
