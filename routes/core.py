from flask import Blueprint, jsonify, session


core_bp = Blueprint('core', __name__)


@core_bp.route('/robots.txt')
def robots():
    return 'User-agent: *\nDisallow: /\n', 200, {'Content-Type': 'text/plain; charset=utf-8'}


@core_bp.route('/settings/time-format/<fmt>', methods=['POST'])
def set_time_format(fmt):
    if fmt in ['12', '24']:
        session['timeFormat'] = fmt
        session.modified = True
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400
