from functools import wraps

from flask import abort, request

from routes import current_department_id, current_department_name, current_role


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_super_admin():
    return current_role() == 'super_admin'


def is_admin():
    return current_role() == 'admin'


def department_id_allowed(department_id):
    if not is_admin():
        return True
    requested_id = _safe_int(department_id)
    return requested_id is not None and requested_id == current_department_id()


def department_name_allowed(department_name, conn=None):
    if not is_admin():
        return True
    current_name = current_department_name(conn)
    return bool(current_name and department_name == current_name)


def admin_department_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin():
            return view(*args, **kwargs)

        department_id = (
            kwargs.get('department_id')
            or request.args.get('department_id')
            or request.form.get('department_id')
        )
        if department_id and not department_id_allowed(department_id):
            abort(403)
        return view(*args, **kwargs)

    return wrapped
