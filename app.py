from flask import Flask, g
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


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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

    return app


if __name__ == '__main__':
    db.init_db()
    db.create_default_users()
    app = create_app()
    app.run(debug=True)
