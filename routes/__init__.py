from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get('role') != 'super_admin':
            flash('صلاحيات غير كافية', 'danger')
            return redirect(url_for('auth.dashboard'))
        return view(*args, **kwargs)
    return wrapped
