import json
import sqlite3

from flask import g

from config import Config

DATABASE = Config.DATABASE
DEFAULT_PERIODS = [
    ('A', 'الفترة أ', '09:00', '12:00', 1, 1),
    ('B', 'الفترة ب', '12:00', '15:00', 1, 2),
    ('C', 'الفترة ج', '15:00', '18:00', 0, 3),
]

DEFAULT_COURSE_CATALOG = [
    (
        'القسم العام',
        1,
        [
            'هندسة وصفية',
            'أسس كهرباء',
            'استاتيكا',
            'تقنية ورش',
            'رياضة 2، 3',
            'كتابة تقارير',
            'مصطلحات فنية',
            'فيزياء نسبية',
        ],
    ),
    (
        'قسم النفط',
        1,
        [
            'مقدمة هندسة نفط',
            'جيولوجيا عامة',
            'كيمياء عضوية',
            'جيولوجيا نفط',
        ],
    ),
    (
        'قسم النفط',
        2,
        [
            'ديناميكا حرارية',
            'ميكانيكا موائع',
            'سريان الموائع',
            'خواص موائع المكمن',
            'خواص صخور المكمن',
            'صخور رسوبية',
            'جيولوجيا تركيبية',
            'معدات حقول النفط',
        ],
    ),
    (
        'قسم النفط',
        3,
        [
            'حفر وتصميم الابار',
            'تقنية سوائل الحفر',
            'هندسة انتاج',
            'هندسة غاز',
            'تطبيقات الحاسوب في الهندسة النفطية',
            'التآكل في الصناعات النفطية',
        ],
    ),
    (
        'قسم النفط',
        4,
        [
            'طرق تحسين ابار النفط',
            'صيانة واصلاح الابار',
            'تقييم المكامن النفطية',
            'استكمال ابار النفط',
            'اقتصاديات هندسة نفط',
        ],
    ),
    (
        'قسم الحاسوب',
        1,
        [
            'برمجة حاسوب',
            'عمارة الحاسوب',
        ],
    ),
    (
        'قسم الحاسوب',
        2,
        [
            'نظم قواعد البيانات',
            'البرمجة المرئية',
            'وسائط متعددة',
            'نظم التشغيل',
            'تراكيب البيانات والخوارزميات',
            'تحليل البيانات باستخدام Excel',
            'إحصاء واحتمالات',
        ],
    ),
    (
        'قسم الحاسوب',
        3,
        [
            'أسس هندسة البرمجيات',
            'تحليل متطلبات البرمجيات',
            'شبكات الحاسوب',
            'قواعد بيانات متقدمة',
            'برمجة الانترنت',
            'تصميم منطقي',
        ],
    ),
    (
        'قسم الحاسوب',
        4,
        [
            'أمن البرمجيات',
            'التجارة الالكترونية',
            'اختبار وجودة البرمجيات',
            'مواضيع مختارة',
            'معالجات دقيقة',
        ],
    ),
    (
        'قسم الاتصالات',
        1,
        [
            'دوائر كهربائية',
            'دوائر الكترونية',
            'ورشة الكترونية',
            'مبادئ هندسة الكترونية',
        ],
    ),
    (
        'قسم الاتصالات',
        2,
        [
            'الكترونات رقمية',
            'معالجات دقيقة',
            'أجهزة قياس كهربائية',
            'فيزياء 2',
            'كهرومغناطيسية',
            'انظمة تحكم',
            'وسائط نقل',
        ],
    ),
    (
        'قسم الاتصالات',
        3,
        [
            'نظم اتصالات',
            'هوائيات',
            'معالجة اشارة رقمية',
            'اتصالات رقمية',
            'انظمة مقسمات والهواتف',
            'انظمة الهواتف المحمولة',
        ],
    ),
    (
        'قسم المدني',
        1,
        [
            'مواد الانشاء',
            'ميكانيكا الجوامد',
        ],
    ),
    (
        'قسم المدني',
        2,
        [
            'خرسانة مسلحة',
            'انشاء مباني',
        ],
    ),
    (
        'قسم المدني',
        3,
        [
            'كميات والمواصفات',
            'ادارة مشاريع هندسية',
        ],
    ),
    (
        'قسم المعماري',
        1,
        [
            'تاريخ عمارة',
            'قوانين المباني',
        ],
    ),
    (
        'قسم المعماري',
        2,
        [
            'تنسيق مواقع',
            'تخطيط اقليمي',
            'انظمة تكيف',
        ],
    ),
    (
        'قسم المعماري',
        3,
        [
            'تصميم معماري',
            'اسكان وتصميم حضري',
        ],
    ),
]

DEFAULT_DEPARTMENTS = [
    ('القسم العام', 2, 1),
    ('قسم الاتصالات', 8, 8),
    ('قسم الحاسوب', 8, 8),
    ('قسم المدني', 8, 8),
    ('قسم المعماري', 8, 8),
    ('قسم النفط', 8, 8),
]

DEFAULT_ROOMS = [
    ('قاعة 1', 'قاعة 1', 'قاعة', 'متاحة', 40, 'الدور الأرضي'),
    ('قاعة 2', 'قاعة 2', 'قاعة', 'متاحة', 40, 'الدور الأرضي'),
    ('قاعة 3', 'قاعة 3', 'قاعة', 'متاحة', 40, 'الدور الأول'),
    ('قاعة 4', 'قاعة 4', 'قاعة', 'متاحة', 40, 'الدور الأول'),
    ('قاعة 5', 'قاعة 5', 'قاعة', 'متاحة', 40, 'الدور الثاني'),
    ('قاعة 6', 'قاعة 6', 'قاعة', 'متاحة', 40, 'الدور الثاني'),
    ('قاعة 7', 'قاعة 7', 'قاعة', 'متاحة', 40, 'الدور الثالث'),
    ('قاعة 8', 'قاعة 8', 'قاعة', 'متاحة', 40, 'الدور الثالث'),
    ('قاعة 9', 'قاعة 9', 'قاعة', 'متاحة', 40, 'الدور الرابع'),
    ('قاعة 10', 'قاعة 10', 'قاعة', 'متاحة', 40, 'الدور الرابع'),
    ('قاعة 11', 'قاعة 11', 'قاعة', 'متاحة', 40, 'الدور الأرضي'),
    ('قاعة 12', 'قاعة 12', 'قاعة', 'متاحة', 40, 'الدور الأول'),
    ('قاعة 13', 'قاعة 13', 'قاعة', 'متاحة', 40, 'الدور الثاني'),
    ('قاعة 14', 'قاعة 14', 'قاعة', 'متاحة', 40, 'الدور الثالث'),
    ('معمل حاسوب 1', 'معمل حاسوب 1', 'معمل', 'متاحة', 30, 'الدور الأرضي'),
    ('معمل حاسوب 2', 'معمل حاسوب 2', 'معمل', 'متاحة', 30, 'الدور الأول'),
    ('معمل حاسوب 3', 'معمل حاسوب 3', 'معمل', 'متاحة', 30, 'الدور الثاني'),
    ('معمل حاسوب 4', 'معمل حاسوب 4', 'معمل', 'متاحة', 30, 'الدور الثالث'),
    ('معمل حاسوب 5', 'معمل حاسوب 5', 'معمل', 'متاحة', 30, 'الدور الرابع'),
    ('معمل إلكترونيات 1', 'معمل إلكترونيات 1', 'معمل', 'متاحة', 25, 'الدور الأرضي'),
    ('معمل إلكترونيات 2', 'معمل إلكترونيات 2', 'معمل', 'متاحة', 25, 'الدور الأول'),
    ('مرسم 1', 'مرسم 1', 'قاعة', 'متاحة', 20, 'الدور الثاني'),
    ('مرسم 2', 'مرسم 2', 'قاعة', 'متاحة', 20, 'الدور الثالث'),
    ('مرسم 3', 'مرسم 3', 'قاعة', 'متاحة', 20, 'الدور الرابع'),
    ('مسرح', 'مسرح', 'مسرح', 'متاحة', 100, 'الدور الأرضي'),
]


def _course_category_letter(department_name):
    normalized = (department_name or '').strip()
    if normalized in {'قسم النفط', 'قسم المدني', 'قسم المعماري'}:
        return 'ه'
    if normalized in {'قسم الحاسوب', 'قسم الاتصالات'}:
        return 'ت'
    return 'ع'


def _seed_default_courses(conn, owner_user_id):
    existing_names = {
        row['name']
        for row in conn.execute(
            'SELECT name FROM courses WHERE user_id = ?',
            (owner_user_id,),
        ).fetchall()
    }
    existing_codes = {
        row['code'].replace('هـ', 'ه')
        for row in conn.execute(
            'SELECT code FROM courses WHERE user_id = ?',
            (owner_user_id,),
        ).fetchall()
    }
    next_sequence_by_prefix = {}
    inserted = 0

    for department, year, course_names in DEFAULT_COURSE_CATALOG:
        prefix = f'{_course_category_letter(department)}{year}'
        next_sequence = next_sequence_by_prefix.get(prefix, 1)

        for name in course_names:
            if name in existing_names:
                continue

            while True:
                code = f'{prefix}{next_sequence:02d}'
                next_sequence += 1
                if code not in existing_codes:
                    break

            conn.execute(
                '''
                INSERT INTO courses (user_id, name, code, department, year, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (owner_user_id, name, code, department, year, None),
            )
            existing_names.add(name)
            existing_codes.add(code)
            inserted += 1

        next_sequence_by_prefix[prefix] = next_sequence

    return inserted


DEFAULT_COURSE_DEPARTMENT_OVERRIDES = {
    'دوائر كهربائية': 'قسم الاتصالات',
    'دوائر الكترونية': 'قسم الاتصالات',
    'ورشة الكترونية': 'قسم الاتصالات',
    'مبادئ هندسة الكترونية': 'قسم الاتصالات',
    'الكترونات رقمية': 'قسم الاتصالات',
    'معالجات دقيقة': 'قسم الاتصالات',
    'أجهزة قياس كهربائية': 'قسم الاتصالات',
    'فيزياء 2': 'قسم الاتصالات',
    'كهرومغناطيسية': 'قسم الاتصالات',
    'انظمة تحكم': 'قسم الاتصالات',
    'وسائط نقل': 'قسم الاتصالات',
    'نظم اتصالات': 'قسم الاتصالات',
    'هوائيات': 'قسم الاتصالات',
    'معالجة اشارة رقمية': 'قسم الاتصالات',
    'اتصالات رقمية': 'قسم الاتصالات',
    'انظمة مقسمات والهواتف': 'قسم الاتصالات',
    'انظمة الهواتف المحمولة': 'قسم الاتصالات',
    'تاريخ عمارة': 'قسم المعماري',
    'قوانين المباني': 'قسم المعماري',
    'تنسيق مواقع': 'قسم المعماري',
    'تخطيط اقليمي': 'قسم المعماري',
    'انظمة تكيف': 'قسم المعماري',
    'تصميم معماري': 'قسم المعماري',
    'اسكان وتصميم حضري': 'قسم المعماري',
    'مواد الانشاء': 'قسم المدني',
    'ميكانيكا الجوامد': 'قسم المدني',
    'خرسانة مسلحة': 'قسم المدني',
    'انشاء مباني': 'قسم المدني',
    'كميات والمواصفات': 'قسم المدني',
    'ادارة مشاريع هندسية': 'قسم المدني',
}

DEFAULT_TEACHERS = [
    'ا. نسيبة بوعلي',
    'د. طارق العطوشي',
    'ا. احمد ابوسروال',
    'د. جلال المنصوري',
    'انتصار الغالى',
    'نسيم الكحلاء',
    'فخرى الزواغى',
    'غادة ابوالسعود',
    'نورية أبو الشواشي',
    'هناء الهاميسي',
    'ابو بكر صالح',
    'رمزي دهان',
    'د. توفيق التلوع',
    'أسامة ابو رويس',
    'شريهان ابوخناتة',
    'يسين ابوسنوقة',
    'نعيمة باكير',
    'ماجدة المالطي',
    'د.طارق المالطي',
    'كامل خمير',
    'مهند الخلاص',
    'عذارى الادريسي',
    'حنان معمر',
    'شكري غميض',
    'دانيا دباب',
    'نادر الغالي',
    'مباسم الحطاب',
    'كريمة عطية',
    'اصالة العزابي',
    'د.حسين الاسود',
    'منيرة صاكي',
    'الهام ابو الشواشي',
    'صفاء قطس',
    'ابو بكر نصر',
    'هاتي الطوشي',
    'عنود الدريس',
    'هنيدة العطوشي',
    'وفاء عطية',
    'سلطان غرية',
    'راحيل المنصوري',
    'دينا بكة',
    'مودة فطيس',
]


def _rebalance_default_courses(conn, owner_user_id):
    updated = 0
    for course_name, department in DEFAULT_COURSE_DEPARTMENT_OVERRIDES.items():
        cursor = conn.execute(
            '''
            UPDATE courses
            SET department = ?
            WHERE user_id = ? AND name = ?
            ''',
            (department, owner_user_id, course_name),
        )
        updated += cursor.rowcount if cursor.rowcount is not None else 0
    return updated


def _seed_default_teachers(conn, owner_user_id):
    existing_names = {
        row['name']
        for row in conn.execute(
            'SELECT name FROM teachers WHERE user_id = ?',
            (owner_user_id,),
        ).fetchall()
    }
    inserted = 0

    for name in DEFAULT_TEACHERS:
        if name in existing_names:
            continue
        conn.execute(
            '''
            INSERT INTO teachers (user_id, name, department, subject)
            VALUES (?, ?, ?, ?)
            ''',
            (owner_user_id, name, '', ''),
        )
        inserted += 1

    return inserted


def _get_column_names(conn, table_name):
    rows = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    return {row[1] for row in rows}


def _ensure_periods_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS period_settings (
            code TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_enabled INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL
        )
        """
    )
    rows = conn.execute('SELECT code, label FROM period_settings').fetchall()
    existing_codes = {row[0] for row in rows}
    existing_labels = {row[0]: row[1] for row in rows}

    for code, label, start_time, end_time, is_enabled, sort_order in DEFAULT_PERIODS:
        if code not in existing_codes:
            conn.execute(
                """
                INSERT INTO period_settings (code, label, start_time, end_time, is_enabled, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (code, label, start_time, end_time, is_enabled, sort_order),
            )
        elif existing_labels.get(code) != label:
            conn.execute(
                'UPDATE period_settings SET label = ? WHERE code = ?',
                (label, code),
            )


def _ensure_history_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            actor_user_id INTEGER,
            actor_username TEXT,
            message TEXT,
            old_value TEXT,
            new_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_history_created_at
        ON history(created_at DESC)
        """
    )


def _serialize_history_value(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return json.dumps(value, ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def _configure_connection(conn):
    conn.text_factory = str
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = MEMORY')
    return conn


def ensure_schema(conn=None):
    should_close = conn is None
    if conn is None:
        conn = sqlite3.connect(DATABASE)
        _configure_connection(conn)

    existing_tables = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    if 'courses' in existing_tables:
        course_columns = _get_column_names(conn, 'courses')
        if 'year' not in course_columns:
            conn.execute('ALTER TABLE courses ADD COLUMN year INTEGER NOT NULL DEFAULT 1')
        if 'notes' not in course_columns:
            conn.execute('ALTER TABLE courses ADD COLUMN notes TEXT')

    if 'history' in existing_tables:
        history_columns = _get_column_names(conn, 'history')
        if 'actor_user_id' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN actor_user_id INTEGER')
        if 'actor_username' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN actor_username TEXT')
        if 'message' not in history_columns:
            conn.execute('ALTER TABLE history ADD COLUMN message TEXT')

    _ensure_periods_table(conn)
    _ensure_history_table(conn)
    conn.commit()

    if should_close:
        conn.close()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        _configure_connection(db)
        ensure_schema(db)
    return db


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)
    db.execute('PRAGMA encoding = "UTF-8"')
    with open('schema.sql', mode='r', encoding='utf-8') as f:
        db.executescript(f.read())
    ensure_schema(db)
    db.commit()
    db.close()


def create_default_users():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)
    from werkzeug.security import generate_password_hash

    users = [
        ('superadmin', generate_password_hash('admin123')),
        ('admin', generate_password_hash('admin123')),
    ]
    for username, password in users:
        exists = db.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone()
        if not exists:
            role = 'super_admin' if username == 'superadmin' else 'admin'
            label = 'General Department' if username == 'superadmin' else 'Default Department'
            db.execute(
                'INSERT INTO users (username, password, role, label) VALUES (?, ?, ?, ?)',
                (username, password, role, label),
            )
    ensure_schema(db)
    db.commit()
    db.close()


def create_default_departments():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)

    ensure_schema(db)

    inserted = 0
    for name, semesters, majors in DEFAULT_DEPARTMENTS:
        exists = db.execute('SELECT 1 FROM departments WHERE name = ?', (name,)).fetchone()
        if exists:
            continue
        db.execute(
            'INSERT INTO departments (name, semesters, majors) VALUES (?, ?, ?)',
            (name, semesters, majors),
        )
        inserted += 1

    db.commit()
    db.close()
    return inserted


def create_default_rooms():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)

    ensure_schema(db)

    inserted = 0
    for name, name_ar, type_, status, capacity, location in DEFAULT_ROOMS:
        exists = db.execute('SELECT 1 FROM rooms WHERE name = ?', (name,)).fetchone()
        if exists:
            continue
        db.execute(
            '''
            INSERT INTO rooms (name, name_ar, type, status, capacity, location)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (name, name_ar, type_, status, capacity, location),
        )
        inserted += 1

    db.commit()
    db.close()
    return inserted


def create_default_courses():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)

    ensure_schema(db)

    super_admin = db.execute(
        "SELECT id FROM users WHERE username = ? OR role = 'super_admin' ORDER BY id LIMIT 1",
        ('superadmin',),
    ).fetchone()
    if super_admin is None:
        db.close()
        return 0

    inserted = _seed_default_courses(db, super_admin['id'])
    _rebalance_default_courses(db, super_admin['id'])
    db.commit()
    db.close()
    return inserted


def create_default_teachers():
    db = sqlite3.connect(DATABASE)
    _configure_connection(db)

    ensure_schema(db)

    super_admin = db.execute(
        "SELECT id FROM users WHERE username = ? OR role = 'super_admin' ORDER BY id LIMIT 1",
        ('superadmin',),
    ).fetchone()
    if super_admin is None:
        db.close()
        return 0

    inserted = _seed_default_teachers(db, super_admin['id'])
    db.commit()
    db.close()
    return inserted


def add_history(
    conn,
    action,
    entity_type,
    entity_id=None,
    actor_user_id=None,
    actor_username=None,
    message=None,
    old_value=None,
    new_value=None,
):
    conn.execute(
        """
        INSERT INTO history (
            action,
            entity_type,
            entity_id,
            actor_user_id,
            actor_username,
            message,
            old_value,
            new_value
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            action,
            entity_type,
            entity_id,
            actor_user_id,
            actor_username,
            message,
            _serialize_history_value(old_value),
            _serialize_history_value(new_value),
        ),
    )
