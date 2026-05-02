from functools import wraps
from flask import session, abort, request

def admin_department_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') == 'admin':
            # تحقق من أن أي department_id في الرابط أو البيانات يطابق session['department_id']
            department_id = (
                kwargs.get('department_id') or
                request.args.get('department_id') or
                request.form.get('department_id')
            )
            if department_id and int(department_id) != int(session['department_id']):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function
