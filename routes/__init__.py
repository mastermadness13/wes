from functools import wraps
from flask import flash, g, redirect, session, url_for

import db


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def current_user_id():
    return _safe_int(session.get('user_id'))


def current_role():
    return session.get('role')


def current_department_id():
    return _safe_int(session.get('department_id'))


def current_department(conn=None):
    """Fetches the current user's department with request-level caching."""
    if 'current_dept_cached' not in g:
        department_id = current_department_id()
        if department_id is None:
            g.current_dept_cached = None
        else:
            connection = conn or db.get_db()
            g.current_dept_cached = connection.execute(
                'SELECT id, name, semesters FROM departments WHERE id = ?', (department_id,)
            ).fetchone()
    return g.current_dept_cached


def current_department_name(conn=None):
    department = current_department(conn)
    return department['name'] if department else None


def has_valid_department_access(conn=None):
    if current_role() != 'admin':
        return True
    return current_department(conn) is not None


def clear_invalid_session():
    preserved_theme = session.get('theme')
    preserved_font_size = session.get('font_size')
    preserved_time_format = session.get('time_format')
    session.clear()
    if preserved_theme:
        session['theme'] = preserved_theme
    if preserved_font_size:
        session['font_size'] = preserved_font_size
    if preserved_time_format:
        session['time_format'] = preserved_time_format


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user_id() is None:
            flash('يجب تسجيل الدخول أولاً.', 'danger')
            return redirect(url_for('auth.login'))
        if not current_role():
            clear_invalid_session()
            flash('انتهت الجلسة الحالية أو أصبحت غير صالحة. يرجى تسجيل الدخول مرة أخرى.', 'danger')
            return redirect(url_for('auth.login'))
        if not has_valid_department_access():
            clear_invalid_session()
            flash('حساب الأدمن غير مرتبط بقسم صالح. تم تسجيل الخروج لحماية النظام.', 'danger')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)

    return wrapped


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get('role') not in allowed_roles:
                flash('ليس لديك صلاحية الوصول إلى هذه الصفحة.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def super_admin_required(view):
    return role_required('super_admin')(view)


def courses_timetable_admin_required(view):
    return role_required('admin', 'super_admin')(view)
