-- Migration: add devices column to rooms
-- Run with the provided script or using sqlite3:
--   sqlite3 <db_path> ".read migrations/2026-04-27_add_devices_to_rooms.sql"

ALTER TABLE rooms ADD COLUMN devices INTEGER DEFAULT 0;
