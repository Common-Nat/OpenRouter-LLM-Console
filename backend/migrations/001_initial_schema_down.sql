-- Rollback for 001_initial_schema.sql
-- Drops all tables created in the initial schema migration
-- WARNING: This will permanently delete all data in these tables

PRAGMA foreign_keys = OFF;

-- Drop tables in reverse order to handle foreign key dependencies
DROP TABLE IF EXISTS usage_logs;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS profiles;
DROP TABLE IF EXISTS models;

-- Drop any schema version tracking if it exists
DROP TABLE IF EXISTS schema_version;

PRAGMA foreign_keys = ON;
