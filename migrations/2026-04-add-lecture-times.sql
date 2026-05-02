-- Migration: Add start_time and end_time to timetable if not exists
ALTER TABLE timetable ADD COLUMN start_time TEXT;
ALTER TABLE timetable ADD COLUMN end_time TEXT;
