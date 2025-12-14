-- Add openrouter_preset column to profiles table
-- This allows profiles to specify model presets (e.g., model@preset/coding)

-- Check if column exists (SQLite doesn't support IF NOT EXISTS for ALTER TABLE)
-- This will fail silently if column already exists when run in migration system
ALTER TABLE profiles ADD COLUMN openrouter_preset TEXT;
