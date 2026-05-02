-- Migration: add department_id to users table and link to departments
ALTER TABLE users ADD COLUMN department_id INTEGER REFERENCES departments(id);
-- Optionally, set department_id for existing admins here manually if needed.