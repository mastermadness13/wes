from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import db
from datetime import datetime

from routes import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db.get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['label'] = user['label']
            if session['role'] != 'super_admin':
                dept = conn.execute('SELECT DISTINCT department FROM courses WHERE user_id = ?', (user['id'],)).fetchone()
                session['department'] = dept['department'] if dept else 'غير محدد'
            else:
                session['department'] = 'جميع الأقسام'
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
    day_names = {
        0: 'الاثنين',  # Monday
        1: 'الثلاثاء',
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد'
    }
    current_day = day_names[datetime.now().weekday()]
    if session.get('role') == 'super_admin':
        users = conn.execute('SELECT * FROM users').fetchall()
        counts = {
            'users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
            'students': conn.execute('SELECT COUNT(*) FROM students').fetchone()[0],
            'teachers': conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0],
            'courses': conn.execute('SELECT COUNT(*) FROM courses').fetchone()[0],
            'timetable': conn.execute('SELECT COUNT(*) FROM timetable').fetchone()[0],
            'departments': conn.execute('SELECT COUNT(*) FROM departments').fetchone()[0],
            'admins': conn.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0],
        }
        # Get departments (assuming label is department)
        departments = conn.execute('SELECT DISTINCT label as name FROM users WHERE label IS NOT NULL').fetchall()
        admins = conn.execute('SELECT username FROM users WHERE role = "admin"').fetchall()
        # Today lectures
        today_lectures = conn.execute('''
            SELECT t.*, c.name as course_name, te.name as teacher_name, t.room as room_name
            FROM timetable t
            JOIN courses c ON t.course_id = c.id
            JOIN teachers te ON t.teacher_id = te.id
            WHERE t.day = ?
        ''', (current_day,)).fetchall()
        recent_activity = conn.execute('''
            SELECT c.name as course_name, te.name as teacher_name
            FROM timetable t
            JOIN courses c ON t.course_id = c.id
            JOIN teachers te ON t.teacher_id = te.id
            ORDER BY t.created_at DESC LIMIT 5
        ''').fetchall()
        return render_template('dashboard/dashboard_admin.html', users=users, counts=counts, departments=departments, admins=admins, today_lectures=today_lectures, recent_activity=recent_activity)
    else:
        counts = {
            'students': conn.execute('SELECT COUNT(*) FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()[0],
            'teachers': conn.execute('SELECT COUNT(*) FROM teachers WHERE user_id = ?', (session['user_id'],)).fetchone()[0],
            'courses': conn.execute('SELECT COUNT(*) FROM courses WHERE user_id = ?', (session['user_id'],)).fetchone()[0],
            'timetable': conn.execute('SELECT COUNT(*) FROM timetable WHERE user_id = ?', (session['user_id'],)).fetchone()[0],
        }
        # Today lectures for user
        today_lectures = conn.execute('''
            SELECT t.*, c.name as course_name, te.name as teacher_name, t.room as room_name
            FROM timetable t
            JOIN courses c ON t.course_id = c.id
            JOIN teachers te ON t.teacher_id = te.id
            WHERE t.user_id = ? AND t.day = ?
        ''', (session['user_id'], current_day)).fetchall()
        recent_activity = conn.execute('''
            SELECT c.name as course_name, te.name as teacher_name
            FROM timetable t
            JOIN courses c ON t.course_id = c.id
            JOIN teachers te ON t.teacher_id = te.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC LIMIT 5
        ''', (session['user_id'],)).fetchall()
        return render_template('dashboard/dashboard_user.html', counts=counts, today_lectures=today_lectures, recent_activity=recent_activity)
