#!/usr/bin/env python3
"""
Add missing columns to guardrail_events table.

This migration adds all the columns that the GuardrailEvent model expects but might not exist in the database:
- response_time_minutes
- acknowledged_by
- acknowledged_at
- resolved_by
- resolved_at
- resolution_notes
- escalated_at
- escalated_to
- priority
- tags
- user_message
- bot_response

Safe to re-run; skips if columns already exist.
"""

import os
import logging
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

TABLE_NAME = 'guardrail_events'

# Columns to add with their SQL types
# Format: (column_name, postgresql_type, sqlite_type, default_value_sql)
COLUMNS_TO_ADD = [
    ('response_time_minutes', 'INTEGER', 'INTEGER', None),
    ('acknowledged_by', 'VARCHAR(50)', 'VARCHAR(50)', None),
    ('acknowledged_at', 'TIMESTAMP WITH TIME ZONE', 'DATETIME', None),
    ('resolved_by', 'VARCHAR(50)', 'VARCHAR(50)', None),
    ('resolved_at', 'TIMESTAMP WITH TIME ZONE', 'DATETIME', None),
    ('resolution_notes', 'TEXT', 'TEXT', None),
    ('escalated_at', 'TIMESTAMP WITH TIME ZONE', 'DATETIME', None),
    ('escalated_to', 'VARCHAR(50)', 'VARCHAR(50)', None),
    ('priority', 'VARCHAR(20)', 'VARCHAR(20)', "'NORMAL'"),
    ('tags', 'VARCHAR(255)', 'VARCHAR(255)', None),
    ('user_message', 'TEXT', 'TEXT', None),
    ('bot_response', 'TEXT', 'TEXT', None),
    ('details', 'JSON', 'TEXT', None),  # Added missing details column
]


def check_column_exists(conn, table_name, column_name, database_url):
    """Check if a column exists in a table"""
    if 'postgresql' in database_url.lower():
        # PostgreSQL check
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name AND column_name = :column_name
        """)
        result = conn.execute(check_sql, {"table_name": table_name, "column_name": column_name}).fetchone()
        return result is not None
    elif 'sqlite' in database_url.lower():
        # SQLite check
        check_sql = text(f"PRAGMA table_info({table_name})")
        result = conn.execute(check_sql).fetchall()
        for row in result:
            if row[1] == column_name:  # SQLite PRAGMA returns (cid, name, type, notnull, dflt_value, pk)
                return True
        return False
    else:
        # Try using SQLAlchemy inspector
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns


def add_column_postgresql(conn, table_name, column_name, column_type, default_value=None):
    """Add column to PostgreSQL table"""
    if default_value:
        alter_sql = text(f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type} DEFAULT {default_value}
        """)
    else:
        alter_sql = text(f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
        """)
    conn.execute(alter_sql)
    logger.info(f"✅ Added column {column_name} ({column_type}) to {table_name}")


def add_column_sqlite(conn, table_name, column_name, column_type):
    """Add column to SQLite table"""
    # SQLite doesn't support all PostgreSQL types, so we simplify
    sqlite_type = 'INTEGER' if 'INTEGER' in column_type else 'TEXT'
    alter_sql = text(f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name} {sqlite_type}
    """)
    conn.execute(alter_sql)
    logger.info(f"✅ Added column {column_name} ({sqlite_type}) to {table_name}")


def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    logger.info(f"Connecting to DB: {database_url}")
    
    engine = create_engine(database_url)
    
    with engine.begin() as conn:
        logger.info(f"Checking table: {TABLE_NAME}")
        
        # Check if table exists
        if 'postgresql' in database_url.lower():
            table_check = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = :table_name
            """)
            table_exists = conn.execute(table_check, {"table_name": TABLE_NAME}).fetchone()
        else:
            # SQLite check
            table_check = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=:table_name
            """)
            table_exists = conn.execute(table_check, {"table_name": TABLE_NAME}).fetchone()
        
        if not table_exists:
            logger.warning(f"⚠️  Table {TABLE_NAME} does not exist. Run init_database.py first.")
            return
        
        # Add each column if it doesn't exist
        added_count = 0
        skipped_count = 0
        is_postgresql = 'postgresql' in database_url.lower()
        
        for column_tuple in COLUMNS_TO_ADD:
            # Handle both old format (2 items) and new format (4 items)
            if len(column_tuple) == 4:
                column_name, pg_type, sqlite_type, default_value = column_tuple
                column_type = pg_type if is_postgresql else sqlite_type
            else:
                # Old format compatibility
                column_name, column_type = column_tuple
                default_value = None
            
            if check_column_exists(conn, TABLE_NAME, column_name, database_url):
                logger.info(f"⏭️  Column {column_name} already exists in {TABLE_NAME}, skipping")
                skipped_count += 1
                continue
            
            # Add the column
            logger.info(f"Adding column {column_name} ({column_type}) to {TABLE_NAME}...")
            
            try:
                if is_postgresql:
                    add_column_postgresql(conn, TABLE_NAME, column_name, column_type, default_value)
                else:
                    add_column_sqlite(conn, TABLE_NAME, column_name, column_type)
                
                added_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to add column {column_name}: {e}")
                # Continue with other columns
                continue
        
        logger.info(f"✅ Migration completed: {added_count} columns added, {skipped_count} columns skipped")
    
    logger.info("=" * 60)
    logger.info("✅ Migration: Add guardrail_event columns - COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception("❌ Migration failed")
        sys.exit(1)
    sys.exit(0)

