#!/usr/bin/env python3
"""
Add missing columns to conversation_sessions table.

This migration adds all the columns that the ConversationSession model expects but might not exist in the database:
- patient_info (JSON)
- risk_level (VARCHAR(20))
- situation (VARCHAR(255))
- is_monitored (BOOLEAN)
- requires_attention (BOOLEAN)
- escalated (BOOLEAN)
- sentiment_score (FLOAT)
- engagement_score (FLOAT)
- satisfaction_score (FLOAT)
- notes (TEXT)
- session_metadata (JSON)

Safe to re-run; skips if columns already exist.
"""

import os
import logging
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TABLE_NAME = 'conversation_sessions'

# Columns to add with their SQL types
# Format: (column_name, postgresql_type, sqlite_type, default_value_sql)
COLUMNS_TO_ADD = [
    ('patient_info', 'JSON', 'TEXT', None),
    ('risk_level', 'VARCHAR(20)', 'VARCHAR(20)', "'LOW'"),
    ('situation', 'VARCHAR(255)', 'VARCHAR(255)', None),
    ('is_monitored', 'BOOLEAN', 'BOOLEAN', 'true'),
    ('requires_attention', 'BOOLEAN', 'BOOLEAN', 'false'),
    ('escalated', 'BOOLEAN', 'BOOLEAN', 'false'),
    ('sentiment_score', 'DOUBLE PRECISION', 'REAL', None),
    ('engagement_score', 'DOUBLE PRECISION', 'REAL', None),
    ('satisfaction_score', 'DOUBLE PRECISION', 'REAL', None),
    ('notes', 'TEXT', 'TEXT', None),
    ('session_metadata', 'JSON', 'TEXT', None),
]

def check_column_exists(conn, column_name: str, is_postgresql: bool) -> bool:
    """Check if a column already exists in the table"""
    if is_postgresql:
        check_sql = text(
            f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{TABLE_NAME}' AND column_name = '{column_name}'
            """
        )
        result = conn.execute(check_sql).fetchone()
        return result is not None
    else:
        # For SQLite, we'll try to add and catch the error
        # For now, return False and let the ALTER TABLE handle it
        return False

def add_column(conn, column_name: str, column_type: str, default_value: str = None, is_postgresql: bool = False):
    """Add a single column to the table"""
    try:
        # Build ALTER TABLE statement
        alter_sql_parts = [f"ALTER TABLE {TABLE_NAME}", f"ADD COLUMN {column_name} {column_type}"]
        
        if default_value is not None:
            alter_sql_parts.append(f"DEFAULT {default_value}")
        
        alter_sql = text(" ".join(alter_sql_parts))
        
        conn.execute(alter_sql)
        logger.info(f"✅ Added column {column_name} to {TABLE_NAME}")
    except Exception as e:
        error_msg = str(e).lower()
        if 'duplicate' in error_msg or 'already exists' in error_msg or 'sqlite3.OperationalError' in str(type(e)):
            logger.info(f"Column {column_name} already exists, skipping.")
        else:
            logger.error(f"Error adding column {column_name}: {e}")
            raise

def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    logger.info(f"Connecting to DB: {database_url}")
    engine = create_engine(database_url)
    
    is_postgresql = 'postgresql' in database_url.lower()

    with engine.begin() as conn:
        for column_name, pg_type, sqlite_type, default_value in COLUMNS_TO_ADD:
            # Determine column type based on database
            column_type = pg_type if is_postgresql else sqlite_type
            
            # Check if column exists (only for PostgreSQL)
            if is_postgresql:
                if check_column_exists(conn, column_name, is_postgresql):
                    logger.info(f"Column {column_name} already exists in {TABLE_NAME}, skipping.")
                    continue
            
            # Add the column
            logger.info(f"Adding column {column_name} ({column_type}) to {TABLE_NAME}...")
            add_column(conn, column_name, column_type, default_value, is_postgresql)

    logger.info("✅ Migration completed successfully")

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("✅ Migration: Add conversation_sessions columns - START")
    logger.info("=" * 60)
    try:
        main()
        logger.info("=" * 60)
        logger.info("✅ Migration: Add conversation_sessions columns - COMPLETE")
        logger.info("=" * 60)
    except Exception as e:
        logger.exception("Migration failed")
        sys.exit(1)
    sys.exit(0)

