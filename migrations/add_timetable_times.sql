-- أضف أعمدة وقت البداية والنهاية لدعم الحصص المرنة
ALTER TABLE timetable ADD COLUMN start_time TEXT;
ALTER TABLE timetable ADD COLUMN end_time TEXT;
