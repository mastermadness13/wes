import secrets
import time

from flask import Flask, g, request, session

import db
from config import Config
from filters import register_filters
from routes.attendance import attendance_bp
from routes.auth import auth_bp
from routes.core import core_bp
from routes.courses import courses_bp
from routes.departments import departments_bp
from routes.history import history_bp
from routes.rooms import rooms_bp
from routes.students import students_bp
from routes.teachers import teachers_bp
from routes.timetable import timetable_bp
from routes.users import users_bp


def configure_app(app):
    app.config.from_object(Config)
    app.config['JSON_AS_ASCII'] = False
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    if app.config.get('SECRET_KEY') == 'change-this-secret':
        app.config['SECRET_KEY'] = secrets.token_hex(32)
    register_filters(app)


def register_request_hooks(app):
    @app.before_request
    def apply_session_policy():
        g.request_started_at = time.perf_counter()
        session.permanent = True

    @app.after_request
    def ensure_utf8_response(response):
        content_type = response.headers.get('Content-Type', '')
        content_type_lower = content_type.lower()
        if (
            ('charset=' not in content_type_lower)
            and (
                content_type_lower.startswith('text/')
                or content_type_lower.startswith('application/json')
            )
        ):
            base_type = content_type or response.mimetype or 'text/plain'
            response.headers['Content-Type'] = f'{base_type}; charset=utf-8'

        started_at = getattr(g, 'request_started_at', None)
        if started_at is not None:
            duration_ms = (time.perf_counter() - started_at) * 1000
            endpoint = request.endpoint or 'unknown'
            log_level = app.logger.warning if duration_ms >= 800 else app.logger.info
            log_level(
                '[request-timing] %s %s -> %s | endpoint=%s | %.2f ms%s',
                request.method,
                request.path,
                response.status_code,
                endpoint,
                duration_ms,
                ' [SLOW]' if duration_ms >= 800 else '',
            )
            response.headers['X-Response-Time-ms'] = f'{duration_ms:.2f}'

        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        return response


def register_blueprints(app):
    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(departments_bp, url_prefix='/departments')
    app.register_blueprint(rooms_bp, url_prefix='/rooms')
    app.register_blueprint(timetable_bp, url_prefix='/timetable')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(history_bp, url_prefix='/history')


def create_app():
    app = Flask(__name__)
    configure_app(app)
    register_request_hooks(app)
    app.teardown_appcontext(db.close_db)
    register_blueprints(app)
    db.bootstrap_defaults()
    return app


if __name__ == '__main__':
    db.init_db()
    db.create_default_users()
    db.create_default_departments()
    db.create_default_rooms()
    db.create_default_courses()
    db.create_default_teachers()
    app = create_app()
    app.run(debug=True)
