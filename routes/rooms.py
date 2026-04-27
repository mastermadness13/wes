from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import db

from routes import login_required, super_admin_required

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/')
@login_required
@super_admin_required
def list_rooms():
    conn = db.get_db()
    rooms = conn.execute('SELECT * FROM rooms ORDER BY name').fetchall()
    return render_template('rooms/list.html', rooms=rooms)

@rooms_bp.route('/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_room():
    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar')
        # إذا لم يُرسل name استخدم name_ar
        if not name and name_ar:
            name = name_ar
        type_ = request.form.get('type')
        status = request.form.get('status')
        capacity = request.form.get('capacity', type=int)
        location = request.form.get('location')

        if not name:
            flash('يجب إدخال اسم القاعة بأي لغة', 'danger')
            return redirect(request.referrer or url_for('rooms.list_rooms'))

        conn = db.get_db()
        try:
            conn.execute('INSERT INTO rooms (name, name_ar, type, status, capacity, location) VALUES (?, ?, ?, ?, ?, ?)',
                        (name, name_ar, type_, status, capacity, location))
            conn.commit()
            flash('تم إضافة القاعة بنجاح', 'success')
        except Exception as e:
            flash(f'خطأ: {str(e)}', 'danger')
        return redirect(url_for('rooms.list_rooms'))

    return render_template('rooms/create.html')

@rooms_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_room(id):
    conn = db.get_db()
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (id,)).fetchone()
    if not room:
        flash('القاعة غير موجودة', 'danger')
        return redirect(url_for('rooms.list_rooms'))

    if request.method == 'POST':
        name = request.form.get('name')
        name_ar = request.form.get('name_ar')
        # إذا لم يُرسل name استخدم name_ar
        if not name and name_ar:
            name = name_ar
        type_ = request.form.get('type')
        status = request.form.get('status')
        capacity = request.form.get('capacity', type=int)
        location = request.form.get('location')

        if not name:
            flash('يجب إدخال اسم القاعة بأي لغة', 'danger')
            return redirect(request.referrer or url_for('rooms.list_rooms'))

        try:
            conn.execute('UPDATE rooms SET name = ?, name_ar = ?, type = ?, status = ?, capacity = ?, location = ? WHERE id = ?',
                        (name, name_ar, type_, status, capacity, location, id))
            conn.commit()
            flash('تم تحديث القاعة بنجاح', 'success')
        except Exception as e:
            flash(f'خطأ: {str(e)}', 'danger')
        return redirect(url_for('rooms.list_rooms'))

    return render_template('rooms/edit.html', room=room)

@rooms_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_room(id):
    conn = db.get_db()
    try:
        conn.execute('DELETE FROM rooms WHERE id = ?', (id,))
        conn.commit()
        flash('تم حذف القاعة بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ: {str(e)}', 'danger')
    return redirect(url_for('rooms.list_rooms'))