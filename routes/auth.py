from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import db

from routes import current_department_name, login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = db.get_db()
        user = conn.execute(
            'SELECT id, username, password, role, label, department_id FROM users WHERE username = ?',
            (username,),
        ).fetchone()
        if user and check_password_hash(user['password'], password):
            department_id = user['department_id'] if 'department_id' in user.keys() else None
            if user['role'] == 'admin' and department_id is None:
                flash('هذا الحساب الإداري غير مرتبط بأي قسم. يرجى مراجعة المشرف العام.', 'danger')
                return render_template('auth/login.html', hide_nav=True)
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['label'] = user['label'] or user['username']
            if user['role'] == 'admin' and department_id is not None:
                session['department_id'] = department_id
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('auth.dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')

    return render_template('auth/login.html', hide_nav=True)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    conn = db.get_db()
    if session.get('role') == 'super_admin':
        total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_courses = conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0]
        total_departments = conn.execute('SELECT COUNT(*) FROM departments').fetchone()[0]
        total_teachers = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]

        # جلب توزيع المقررات للأعمدة البيانية
        course_distribution = conn.execute('''
            SELECT department, COUNT(*) as count 
            FROM courses 
            GROUP BY department 
            ORDER BY count DESC
        ''').fetchall()

        course_dist_list = [dict(row) for row in course_distribution]
        max_dist = max([row['count'] for row in course_dist_list]) if course_dist_list else 0

        return render_template(
            'auth/dashboard.html',
            is_super_admin=True,
            total_users=total_users,
            total_courses=total_courses,
            total_departments=total_departments,
            total_teachers=total_teachers,
            course_distribution=course_dist_list,
            max_course_distribution=max_dist
        )
    else:
        department_name = current_department_name(conn)
        dept_courses = conn.execute(
            'SELECT COUNT(*) FROM courses WHERE department = ?',
            (department_name,)
        ).fetchone()[0] if department_name else 0

        return render_template(
            'auth/dashboard.html',
            is_super_admin=False,
            department_name=department_name,
            department_courses=dept_courses
        )
