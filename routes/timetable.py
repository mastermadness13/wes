from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

import db
from routes import courses_timetable_admin_required, login_required, super_admin_required


timetable_bp = Blueprint('timetable', __name__)

DAY_NAMES = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
DAY_LABELS = {day: day for day in DAY_NAMES}


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_time(value):
    return datetime.strptime(value, '%H:%M').time()


def _minutes(time_value):
    return time_value.hour * 60 + time_value.minute


def _time_ranges_overlap(start_a, end_a, start_b, end_b):
    return _minutes(start_a) < _minutes(end_b) and _minutes(start_b) < _minutes(end_a)


def _get_periods(conn, enabled_only=False):
    sql = 'SELECT code, label, start_time, end_time, is_enabled, sort_order FROM period_settings'
    if enabled_only:
        sql += ' WHERE is_enabled = 1'
    sql += ' ORDER BY sort_order, code'
    periods = []
    for row in conn.execute(sql).fetchall():
        periods.append(
            {
                'code': row['code'],
                'label': row['label'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'is_enabled': bool(row['is_enabled']),
                'sort_order': row['sort_order'],
                'start_obj': _parse_time(row['start_time']),
                'end_obj': _parse_time(row['end_time']),
            }
        )
    return periods


def _period_map(conn):
    return {period['code']: period for period in _get_periods(conn, enabled_only=False)}


def _validate_period_definitions(periods):
    enabled = [period for period in periods if period['is_enabled']]
    if not enabled:
        return 'At least one period must be enabled.'

    enabled.sort(key=lambda item: item['sort_order'])
    if enabled[0]['start_time'] != '09:00':
        return 'The first enabled period must start at 09:00.'

    for period in enabled:
        if _minutes(period['start_obj']) >= _minutes(period['end_obj']):
            return f"{period['label']} must end after it starts."

    for index, current in enumerate(enabled):
        for other in enabled[index + 1:]:
            if _time_ranges_overlap(current['start_obj'], current['end_obj'], other['start_obj'], other['end_obj']):
                return f"{current['label']} overlaps with {other['label']}."

    return None


def _periods_from_form(form):
    periods = []
    for code in ['A', 'B', 'C']:
        start_value = (form.get(f'{code}_start') or '').strip()
        end_value = (form.get(f'{code}_end') or '').strip()
        label = (form.get(f'{code}_label') or f'Period {code}').strip()
        enabled = 1 if form.get(f'{code}_enabled') == '1' else 0
        try:
            start_obj = _parse_time(start_value)
            end_obj = _parse_time(end_value)
        except ValueError:
            return None, 'Time must use HH:MM format.'
        periods.append(
            {
                'code': code,
                'label': label,
                'start_time': start_value,
                'end_time': end_value,
                'is_enabled': enabled,
                'sort_order': {'A': 1, 'B': 2, 'C': 3}[code],
                'start_obj': start_obj,
                'end_obj': end_obj,
            }
        )
    return periods, None


def _build_allowed_semesters(selected_department_name, department_semester_map):
    fallback = [1, 2, 3, 4, 5, 6, 7]
    if selected_department_name and selected_department_name in department_semester_map:
        max_sem = max(1, int(department_semester_map[selected_department_name]))
        return list(range(1, max_sem + 1))
    if department_semester_map:
        values = set()
        for max_sem in department_semester_map.values():
            values.update(range(1, max(1, int(max_sem)) + 1))
        if values:
            return sorted(values)
    return fallback


def _fetch_departments(conn):
    return conn.execute('SELECT id, name, semesters FROM departments ORDER BY name').fetchall()


def _fetch_courses(conn, include_all=False, owner_user_id=None):
    if include_all:
        rows = conn.execute(
            """
            SELECT c.*, u.username AS owner_username, u.label AS owner_label
            FROM courses c
            LEFT JOIN users u ON u.id = c.user_id
            ORDER BY c.department, c.year, c.name
            """
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM courses WHERE user_id = ? ORDER BY department, year, name',
            (owner_user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _fetch_teachers(conn, owner_user_id=None, include_all=False):
    if include_all:
        rows = conn.execute(
            """
            SELECT t.*, u.username AS owner_username
            FROM teachers t
            LEFT JOIN users u ON u.id = t.user_id
            ORDER BY t.department, t.name
            """
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM teachers WHERE user_id = ? ORDER BY department, name',
            (owner_user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _fetch_rooms(conn):
    rows = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    return [dict(row) for row in rows]


def _entry_with_relations(conn, entry_id):
    return conn.execute(
        """
        SELECT t.*, c.name AS course_name, c.department AS course_department,
               te.name AS teacher_name,
               r.name AS room_name, r.name_ar AS room_name_ar,
               u.username AS owner_username, u.label AS owner_label
        FROM timetable t
        JOIN courses c ON c.id = t.course_id
        JOIN teachers te ON te.id = t.teacher_id
        JOIN rooms r ON r.id = t.room_id
        LEFT JOIN users u ON u.id = t.user_id
        WHERE t.id = ?
        """,
        (entry_id,),
    ).fetchone()


def _can_access_entry(entry):
    return bool(entry and (session.get('role') == 'super_admin' or entry['user_id'] == session.get('user_id')))


def _can_delete_critical():
    return session.get('role') == 'super_admin'


def _history_actor():
    return session.get('user_id'), session.get('username') or session.get('label') or 'System'


def _timetable_history_message(action, entry):
    actor_username = session.get('username') or 'System'
    course_name = entry.get('course_name') or f"Course #{entry.get('course_id')}"
    teacher_name = entry.get('teacher_name') or f"Teacher #{entry.get('teacher_id')}"
    room_name = entry.get('room_name_ar') or entry.get('room_name') or f"Room #{entry.get('room_id')}"
    day = entry.get('day') or ''
    semester = entry.get('semester') or ''
    section = entry.get('section') or ''
    action_word = {'ADD': 'added', 'EDIT': 'updated', 'DELETE': 'deleted'}.get(action, 'changed')
    return f"{actor_username} {action_word} timetable entry for {course_name} on {day}, semester {semester}, period {section}, room {room_name}, teacher {teacher_name}."


def _teacher_allowed(conn, teacher_id, owner_user_id):
    if session.get('role') == 'super_admin':
        return conn.execute('SELECT id FROM teachers WHERE id = ?', (teacher_id,)).fetchone() is not None
    return conn.execute(
        'SELECT id FROM teachers WHERE id = ? AND user_id = ?',
        (teacher_id, owner_user_id),
    ).fetchone() is not None


def _room_exists(conn, room_id):
    return conn.execute('SELECT id FROM rooms WHERE id = ?', (room_id,)).fetchone() is not None


def _course_allowed(conn, course_id, owner_user_id):
    if session.get('role') == 'super_admin':
        return conn.execute('SELECT id FROM courses WHERE id = ?', (course_id,)).fetchone() is not None
    return conn.execute(
        'SELECT id FROM courses WHERE id = ? AND user_id = ?',
        (course_id, owner_user_id),
    ).fetchone() is not None


def _validate_owner_resources(conn, owner_user_id, course_id, teacher_id, room_id):
    if not _course_allowed(conn, course_id, owner_user_id):
        return 'The selected course is not available.'
    if not _teacher_allowed(conn, teacher_id, owner_user_id):
        return 'The selected teacher is not available.'
    if not _room_exists(conn, room_id):
        return 'The selected room was not found.'
    return None


def _resolve_owner_user_id(raw_user_id, default_user_id):
    if session.get('role') == 'super_admin':
        parsed = _safe_int(raw_user_id)
        return parsed or default_user_id
    return default_user_id


def _validate_schedule_conflicts(conn, *, day, semester, period_code, teacher_id, room_id, exclude_entry_id=None):
    period_lookup = _period_map(conn)
    target_period = period_lookup.get(period_code)
    if not target_period or not target_period['is_enabled']:
        return 'The selected period is disabled.'

    sql = 'SELECT id, section, teacher_id, room_id FROM timetable WHERE day = ? AND semester = ?'
    params = [day, semester]
    if exclude_entry_id is not None:
        sql += ' AND id != ?'
        params.append(exclude_entry_id)

    for row in conn.execute(sql, params).fetchall():
        existing_period = period_lookup.get(row['section'])
        if not existing_period or not existing_period['is_enabled']:
            continue
        if not _time_ranges_overlap(target_period['start_obj'], target_period['end_obj'], existing_period['start_obj'], existing_period['end_obj']):
            continue
        if row['room_id'] == room_id:
            return 'This room is already booked at the same time.'
        if row['teacher_id'] == teacher_id:
            return 'This teacher is already busy at the same time.'

    return None


def _ensure_selection(records, selected_id, conn, table_name):
    if selected_id and not any(item['id'] == selected_id for item in records):
        row = conn.execute(f'SELECT * FROM {table_name} WHERE id = ?', (selected_id,)).fetchone()
        if row:
            records.insert(0, dict(row))
    return records


def _room_availability_rows(conn, day, semester, period_code, exclude_entry_id=None):
    rooms = _fetch_rooms(conn)
    if not rooms:
        return []

    period_lookup = _period_map(conn)
    target_period = period_lookup.get(period_code)
    if not target_period:
        return [{**dict(room), 'is_available': True} for room in rooms]

    entries = conn.execute('SELECT id, room_id, section FROM timetable WHERE day = ? AND semester = ?', (day, semester)).fetchall()
    blocked_ids = set()
    for entry in entries:
        if exclude_entry_id is not None and entry['id'] == exclude_entry_id:
            continue
        existing_period = period_lookup.get(entry['section'])
        if not existing_period:
            continue
        if _time_ranges_overlap(target_period['start_obj'], target_period['end_obj'], existing_period['start_obj'], existing_period['end_obj']):
            blocked_ids.add(entry['room_id'])

    room_rows = []
    for room in rooms:
        room_dict = dict(room)
        room_dict['is_available'] = room_dict['id'] not in blocked_ids
        room_rows.append(room_dict)
    return room_rows


def _available_teachers(conn, day, semester, period_code, owner_user_id, exclude_entry_id=None):
    teachers = _fetch_teachers(conn, owner_user_id=owner_user_id, include_all=session.get('role') == 'super_admin')
    period_lookup = _period_map(conn)
    target_period = period_lookup.get(period_code)
    if not target_period:
        return []

    entries = conn.execute('SELECT id, teacher_id, section FROM timetable WHERE day = ? AND semester = ?', (day, semester)).fetchall()
    blocked_ids = set()
    for entry in entries:
        if exclude_entry_id is not None and entry['id'] == exclude_entry_id:
            continue
        existing_period = period_lookup.get(entry['section'])
        if not existing_period:
            continue
        if _time_ranges_overlap(target_period['start_obj'], target_period['end_obj'], existing_period['start_obj'], existing_period['end_obj']):
            blocked_ids.add(entry['teacher_id'])

    return [teacher for teacher in teachers if teacher['id'] not in blocked_ids]


@timetable_bp.route('/api/available-rooms')
@login_required
@courses_timetable_admin_required
def available_rooms():
    conn = db.get_db()
    day = (request.args.get('day') or '').strip()
    semester = _safe_int(request.args.get('semester'))
    period_code = (request.args.get('section') or request.args.get('period_code') or '').strip()
    exclude_id = _safe_int(request.args.get('exclude_id'))
    if not day or semester is None or not period_code:
        return jsonify({'rooms': [], 'error': 'day, semester, period_code are required'}), 400
    return jsonify({'rooms': _room_availability_rows(conn, day, semester, period_code, exclude_entry_id=exclude_id)})


@timetable_bp.route('/api/available-teachers')
@login_required
@courses_timetable_admin_required
def available_teachers():
    conn = db.get_db()
    day = (request.args.get('day') or '').strip()
    semester = _safe_int(request.args.get('semester'))
    period_code = (request.args.get('section') or request.args.get('period_code') or '').strip()
    exclude_id = _safe_int(request.args.get('exclude_id'))
    if not day or semester is None or not period_code:
        return jsonify({'teachers': [], 'error': 'day, semester, period_code are required'}), 400
    teachers = _available_teachers(conn, day, semester, period_code, session['user_id'], exclude_entry_id=exclude_id)
    return jsonify({'teachers': [{'id': teacher['id'], 'name': teacher['name']} for teacher in teachers]})


@timetable_bp.route('/period-settings', methods=['POST'])
@login_required
@super_admin_required
def update_period_settings():
    conn = db.get_db()
    periods, form_error = _periods_from_form(request.form)
    if form_error:
        flash(form_error, 'danger')
        return redirect(url_for('timetable.list_timetable'))
    validation_error = _validate_period_definitions(periods)
    if validation_error:
        flash(validation_error, 'danger')
        return redirect(url_for('timetable.list_timetable'))
    for period in periods:
        conn.execute('UPDATE period_settings SET label = ?, start_time = ?, end_time = ?, is_enabled = ?, sort_order = ? WHERE code = ?', (period['label'], period['start_time'], period['end_time'], period['is_enabled'], period['sort_order'], period['code']))
    conn.commit()
    flash('Period settings saved successfully.', 'success')
    return redirect(url_for('timetable.list_timetable'))


@timetable_bp.route('/')
@login_required
@courses_timetable_admin_required
def list_timetable():
    conn = db.get_db()
    selected_department_id = request.args.get('department_id', '')
    selected_user_id = request.args.get('user_id', '')
    selected_semesters_raw = request.args.getlist('semester')

    departments_rows = _fetch_departments(conn)
    departments = [dict(row) for row in departments_rows]
    department_semester_map = {row['name']: row['semesters'] for row in departments_rows}
    selected_department_name = ''
    if selected_department_id:
        selected = conn.execute('SELECT name FROM departments WHERE id = ?', (selected_department_id,)).fetchone()
        selected_department_name = selected['name'] if selected else ''

    allowed_semesters = _build_allowed_semesters(selected_department_name, department_semester_map)
    selected_semesters = [int(value) for value in selected_semesters_raw if str(value).isdigit() and int(value) in allowed_semesters]
    if not selected_semesters:
        selected_semesters = [allowed_semesters[0]]

    enabled_periods = _get_periods(conn, enabled_only=True)
    sql = """
        SELECT t.*, c.name AS course_name, c.department AS course_department,
               te.name AS teacher_name,
               r.name AS room_name, r.name_ar AS room_name_ar,
               u.username AS owner_username, u.label AS owner_label
        FROM timetable t
        JOIN courses c ON c.id = t.course_id
        JOIN teachers te ON te.id = t.teacher_id
        JOIN rooms r ON r.id = t.room_id
        LEFT JOIN users u ON u.id = t.user_id
        WHERE t.semester IN ({})
    """.format(','.join('?' for _ in selected_semesters))
    params = list(selected_semesters)

    if session.get('role') != 'super_admin':
        sql += ' AND t.user_id = ?'
        params.append(session['user_id'])
    elif selected_user_id:
        sql += ' AND t.user_id = ?'
        params.append(selected_user_id)

    if selected_department_name:
        sql += ' AND c.department = ?'
        params.append(selected_department_name)

    sql += ' ORDER BY t.day, t.semester, t.section, t.created_at'
    rows = conn.execute(sql, params).fetchall()

    timetable = {}
    for row in rows:
        timetable.setdefault(row['day'], {}).setdefault(row['semester'], {})[row['section']] = dict(row)

    users = []
    if session.get('role') == 'super_admin':
        users = conn.execute('SELECT id, username, role FROM users ORDER BY username').fetchall()

    current_owner_id = session['user_id'] if session.get('role') != 'super_admin' else _safe_int(selected_user_id, session['user_id'])
    courses = _fetch_courses(conn, include_all=session.get('role') == 'super_admin', owner_user_id=current_owner_id)
    teachers = _fetch_teachers(conn, owner_user_id=current_owner_id, include_all=session.get('role') == 'super_admin')
    rooms = _fetch_rooms(conn)
    period_settings = _get_periods(conn, enabled_only=False)

    return render_template(
        'timetable/list.html',
        timetable=timetable,
        days=DAY_NAMES,
        day_labels=DAY_LABELS,
        enabled_periods=enabled_periods,
        period_settings=period_settings,
        selected_department_id=selected_department_id,
        selected_semesters=selected_semesters,
        allowed_semesters=allowed_semesters,
        departments=departments,
        selected_department_name=selected_department_name,
        users=users,
        courses=courses,
        teachers=teachers,
        rooms=rooms,
        can_delete_critical=_can_delete_critical(),
    )


@timetable_bp.route('/create', methods=['GET', 'POST'])
@login_required
@courses_timetable_admin_required
def create_timetable():
    conn = db.get_db()
    enabled_periods = _get_periods(conn, enabled_only=True)
    default_day = request.args.get('day', DAY_NAMES[0])
    default_semester = _safe_int(request.args.get('semester'), 1)
    default_period_code = request.args.get('section', enabled_periods[0]['code'] if enabled_periods else 'A')

    if request.method == 'POST':
        day = request.form['day']
        semester = _safe_int(request.form['semester'])
        period_code = request.form['section']
        course_id = _safe_int(request.form['course_id'])
        teacher_id = _safe_int(request.form['teacher_id'])
        room_id = _safe_int(request.form['room_id'])
        owner_user_id = session['user_id']

        resource_error = _validate_owner_resources(conn, owner_user_id, course_id, teacher_id, room_id)
        if resource_error:
            flash(resource_error, 'danger')
            return redirect(url_for('timetable.create_timetable'))

        conflict_error = _validate_schedule_conflicts(conn, day=day, semester=semester, period_code=period_code, teacher_id=teacher_id, room_id=room_id)
        if conflict_error:
            flash(conflict_error, 'danger')
            return redirect(url_for('timetable.create_timetable'))

        cursor = conn.execute('INSERT INTO timetable (user_id, day, semester, section, course_id, teacher_id, room_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (owner_user_id, day, semester, period_code, course_id, teacher_id, room_id))
        entry_id = cursor.lastrowid
        entry = _entry_with_relations(conn, entry_id)
        db.add_history(
            conn,
            'ADD',
            'timetable',
            entry_id,
            *_history_actor(),
            message=_timetable_history_message('ADD', dict(entry)),
            new_value=dict(entry),
        )
        conn.commit()
        flash('Timetable entry created successfully.', 'success')
        return redirect(url_for('timetable.list_timetable'))

    initial_rooms = _room_availability_rows(conn, default_day, default_semester, default_period_code)
    initial_teachers = _available_teachers(conn, default_day, default_semester, default_period_code, session['user_id'])

    return render_template(
        'timetable/create.html',
        days=DAY_NAMES,
        enabled_periods=enabled_periods,
        courses=_fetch_courses(conn, include_all=session.get('role') == 'super_admin', owner_user_id=session['user_id']),
        teachers=_fetch_teachers(conn, owner_user_id=session['user_id'], include_all=session.get('role') == 'super_admin'),
        initial_rooms=initial_rooms,
        initial_teachers=initial_teachers,
        default_day=default_day,
        default_semester=default_semester,
        default_period_code=default_period_code,
    )


@timetable_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@courses_timetable_admin_required
def edit_timetable(id):
    conn = db.get_db()
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (id,)).fetchone()
    if not _can_access_entry(entry):
        flash('You are not allowed to edit this entry.', 'danger')
        return redirect(url_for('timetable.list_timetable'))

    if request.method == 'POST':
        day = request.form['day']
        semester = _safe_int(request.form['semester'])
        period_code = request.form['section']
        course_id = _safe_int(request.form['course_id'])
        teacher_id = _safe_int(request.form['teacher_id'])
        room_id = _safe_int(request.form['room_id'])
        owner_user_id = session['user_id']

        resource_error = _validate_owner_resources(conn, owner_user_id, course_id, teacher_id, room_id)
        if resource_error:
            flash(resource_error, 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        conflict_error = _validate_schedule_conflicts(conn, day=day, semester=semester, period_code=period_code, teacher_id=teacher_id, room_id=room_id, exclude_entry_id=id)
        if conflict_error:
            flash(conflict_error, 'danger')
            return redirect(url_for('timetable.edit_timetable', id=id))

        old_entry = _entry_with_relations(conn, id)
        conn.execute('UPDATE timetable SET user_id = ?, day = ?, semester = ?, section = ?, course_id = ?, teacher_id = ?, room_id = ? WHERE id = ?', (owner_user_id, day, semester, period_code, course_id, teacher_id, room_id, id))
        updated = _entry_with_relations(conn, id)
        db.add_history(
            conn,
            'EDIT',
            'timetable',
            id,
            *_history_actor(),
            message=_timetable_history_message('EDIT', dict(updated)),
            old_value=dict(old_entry) if old_entry else None,
            new_value=dict(updated) if updated else None,
        )
        conn.commit()
        flash('Timetable entry updated successfully.', 'success')
        return redirect(url_for('timetable.list_timetable'))

    enabled_periods = _get_periods(conn, enabled_only=True)
    available_rooms = _room_availability_rows(conn, entry['day'], entry['semester'], entry['section'], exclude_entry_id=id)
    available_teachers = _available_teachers(conn, entry['day'], entry['semester'], entry['section'], session['user_id'], exclude_entry_id=id)
    available_teachers = _ensure_selection(available_teachers, entry['teacher_id'], conn, 'teachers')

    return render_template(
        'timetable/edit.html',
        entry=entry,
        days=DAY_NAMES,
        enabled_periods=enabled_periods,
        courses=_fetch_courses(conn, include_all=session.get('role') == 'super_admin', owner_user_id=session['user_id']),
        teachers=_fetch_teachers(conn, owner_user_id=session['user_id'], include_all=session.get('role') == 'super_admin'),
        available_rooms=available_rooms,
        available_teachers=available_teachers,
        can_delete_critical=_can_delete_critical(),
    )


@timetable_bp.route('/api/quick-add', methods=['POST'])
@login_required
@courses_timetable_admin_required
def quick_add_from_cell():
    payload = request.get_json(silent=True) or {}
    conn = db.get_db()
    day = (payload.get('day') or '').strip()
    semester = _safe_int(payload.get('semester'))
    period_code = (payload.get('section') or payload.get('period_code') or '').strip()
    course_id = _safe_int(payload.get('course_id'))
    teacher_id = _safe_int(payload.get('teacher_id'))
    room_id = _safe_int(payload.get('room_id'))

    if not all([day, semester is not None, period_code, course_id, teacher_id, room_id]):
        return jsonify({'ok': False, 'message': 'All fields are required.'}), 400
    resource_error = _validate_owner_resources(conn, session['user_id'], course_id, teacher_id, room_id)
    if resource_error:
        return jsonify({'ok': False, 'message': resource_error}), 400
    conflict_error = _validate_schedule_conflicts(conn, day=day, semester=semester, period_code=period_code, teacher_id=teacher_id, room_id=room_id)
    if conflict_error:
        return jsonify({'ok': False, 'message': conflict_error}), 409

    cursor = conn.execute('INSERT INTO timetable (user_id, day, semester, section, course_id, teacher_id, room_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (session['user_id'], day, semester, period_code, course_id, teacher_id, room_id))
    entry_id = cursor.lastrowid
    entry = _entry_with_relations(conn, entry_id)
    db.add_history(
        conn,
        'ADD',
        'timetable',
        entry_id,
        *_history_actor(),
        message=_timetable_history_message('ADD', dict(entry)),
        new_value=dict(entry),
    )
    conn.commit()
    return jsonify({'ok': True, 'entry': dict(entry), 'message': 'Timetable entry created successfully.'}), 201


@timetable_bp.route('/api/edit-entry', methods=['POST'])
@login_required
@courses_timetable_admin_required
def edit_entry():
    payload = request.get_json(silent=True) or {}
    conn = db.get_db()
    entry_id = _safe_int(payload.get('lecture_id'))
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (entry_id,)).fetchone()
    if not _can_access_entry(entry):
        return jsonify({'ok': False, 'message': 'Not allowed.'}), 403

    day = (payload.get('day') or '').strip()
    semester = _safe_int(payload.get('semester'))
    period_code = (payload.get('section') or payload.get('period_code') or '').strip()
    course_id = _safe_int(payload.get('course_id'))
    teacher_id = _safe_int(payload.get('teacher_id'))
    room_id = _safe_int(payload.get('room_id'))

    resource_error = _validate_owner_resources(conn, session['user_id'], course_id, teacher_id, room_id)
    if resource_error:
        return jsonify({'ok': False, 'message': resource_error}), 400
    conflict_error = _validate_schedule_conflicts(conn, day=day, semester=semester, period_code=period_code, teacher_id=teacher_id, room_id=room_id, exclude_entry_id=entry_id)
    if conflict_error:
        return jsonify({'ok': False, 'message': conflict_error}), 409

    old_entry = _entry_with_relations(conn, entry_id)
    conn.execute('UPDATE timetable SET user_id = ?, day = ?, semester = ?, section = ?, course_id = ?, teacher_id = ?, room_id = ? WHERE id = ?', (session['user_id'], day, semester, period_code, course_id, teacher_id, room_id, entry_id))
    updated = _entry_with_relations(conn, entry_id)
    db.add_history(
        conn,
        'EDIT',
        'timetable',
        entry_id,
        *_history_actor(),
        message=_timetable_history_message('EDIT', dict(updated)),
        old_value=dict(old_entry) if old_entry else None,
        new_value=dict(updated) if updated else None,
    )
    conn.commit()
    return jsonify({'ok': True, 'entry': dict(updated), 'message': 'Timetable entry updated successfully.'})


@timetable_bp.route('/api/delete-entry', methods=['POST'])
@login_required
@courses_timetable_admin_required
def delete_entry():
    if not _can_delete_critical():
        return jsonify({'ok': False, 'message': 'Only the super admin can delete timetable entries.'}), 403

    payload = request.get_json(silent=True) or {}
    entry_id = _safe_int(payload.get('lecture_id'))
    conn = db.get_db()
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (entry_id,)).fetchone()
    if not _can_access_entry(entry):
        return jsonify({'ok': False, 'message': 'Not allowed.'}), 403

    old_entry = _entry_with_relations(conn, entry_id)
    db.add_history(
        conn,
        'DELETE',
        'timetable',
        entry_id,
        *_history_actor(),
        message=_timetable_history_message('DELETE', dict(old_entry) if old_entry else {}),
        old_value=dict(old_entry) if old_entry else None,
    )
    conn.execute('DELETE FROM timetable WHERE id = ?', (entry_id,))
    conn.commit()
    return jsonify({'ok': True, 'message': 'Timetable entry deleted successfully.'})
