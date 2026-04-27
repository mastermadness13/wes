import json

from flask import Blueprint, render_template, request

import db
from routes import login_required, super_admin_required

history_bp = Blueprint('history', __name__)


def _display_history_value(raw_value):
    if raw_value in (None, ''):
        return '—'
    try:
        parsed = json.loads(raw_value)
    except Exception:
        return str(raw_value)
    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    if parsed in (None, ''):
        return '—'
    return str(parsed)


@history_bp.route('/')
@login_required
@super_admin_required
def list_history():
    conn = db.get_db()
    action = (request.args.get('action') or '').strip().upper()
    entity_type = (request.args.get('entity_type') or '').strip().lower()

    sql = '''
        SELECT h.*, u.label AS actor_label
        FROM history h
        LEFT JOIN users u ON u.id = h.actor_user_id
        WHERE 1 = 1
    '''
    params = []
    if action:
        sql += ' AND h.action = ?'
        params.append(action)
    if entity_type:
        sql += ' AND h.entity_type = ?'
        params.append(entity_type)
    sql += ' ORDER BY h.created_at DESC, h.id DESC'

    rows = conn.execute(sql, params).fetchall()
    entries = []
    for row in rows:
        item = dict(row)
        item['old_display'] = _display_history_value(item.get('old_value'))
        item['new_display'] = _display_history_value(item.get('new_value'))
        actor_name = item.get('actor_username') or item.get('actor_label') or 'System'
        item['actor_name'] = actor_name
        if not item.get('message'):
            verb = {'ADD': 'added', 'EDIT': 'updated', 'DELETE': 'deleted'}.get(item['action'], 'changed')
            item['message'] = f"{actor_name} {verb} {item['entity_type']} #{item['entity_id']}"
        entries.append(item)

    return render_template('history/list.html', entries=entries, action=action, entity_type=entity_type)
