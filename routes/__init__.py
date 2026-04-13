from functools import wraps
from flask import flash, redirect, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً.', 'danger')
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
