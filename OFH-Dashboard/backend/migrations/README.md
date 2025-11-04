# Database Migrations

This directory contains database migration scripts to update the database schema.

## Running Migrations

### Individual Migration
```bash
python migrations/20251104_add_message_content_column.py
```

### Using Virtual Environment
```bash
# Activate venv first
.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
venv\Scripts\activate.bat   # Windows CMD

# Then run migration
python migrations/20251104_add_message_content_column.py
```

## Available Migrations

### 20251104_add_message_content_column.py
- **Purpose**: Adds `message_content` column to `guardrail_events` table
- **Status**: Safe to re-run (idempotent)
- **Database Support**: PostgreSQL and SQLite

### 20251030_convert_is_deleted_boolean.py
- **Purpose**: Converts `is_deleted` columns from integer to boolean
- **Status**: Safe to re-run (idempotent)
- **Database Support**: PostgreSQL

## Notes

- All migrations are designed to be idempotent (safe to run multiple times)
- Migrations check for existing columns/structures before modifying
- Always backup your database before running migrations in production
- Migrations are applied in chronological order (by date prefix)

