import secrets
from flask import Flask, g, session
from config import Config
import db

from routes.auth import auth_bp
from routes.users import users_bp
from routes.students import students_bp
from routes.teachers import teachers_bp
from routes.courses import courses_bp
from routes.timetable import timetable_bp
from routes.attendance import attendance_bp
from routes.departments import departments_bp
from routes.rooms import rooms_bp
from routes.history import history_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['JSON_AS_ASCII'] = False
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    if app.config.get('SECRET_KEY') == 'change-this-secret':
        app.config['SECRET_KEY'] = secrets.token_hex(32)

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
        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        return response

    @app.before_request
    def apply_session_policy():
        session.permanent = True

    @app.route('/robots.txt')
    def robots():
        return 'User-agent: *\nDisallow: /\n', 200, {'Content-Type': 'text/plain; charset=utf-8'}

    app.teardown_appcontext(db.close_db)

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

    db.create_default_users()
    db.create_default_departments()
    db.create_default_rooms()
    db.create_default_courses()
    db.create_default_teachers()

    return app


if __name__ == '__main__':
    db.init_db()
    db.create_default_users()
    db.create_default_departments()
    db.create_default_rooms()
    db.create_default_courses()
    db.create_default_teachers()
    app = create_app()
    app.run(debug=True )
