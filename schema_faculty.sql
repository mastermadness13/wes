-- جدول أعضاء هيئة التدريس والمعيدين
CREATE TABLE IF NOT EXISTS faculty_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    academic_number TEXT NOT NULL,
    national_id TEXT NOT NULL UNIQUE,
    qualification TEXT NOT NULL, -- دبلوم/بكالوريوس/ماجستير
    academic_rank TEXT NOT NULL, -- أستاذ/أستاذ مشارك/أستاذ مساعد/محاضر/محاضر مساعد/أستاذ متعاون
    category TEXT NOT NULL,      -- عضو هيئة تدريس متفرغ/متعاون/معيد
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- فهرس لضمان عدم تكرار الرقم الأكاديمي مستقبلاً (اختياري)
CREATE UNIQUE INDEX IF NOT EXISTS idx_faculty_academic_number ON faculty_members(academic_number);
