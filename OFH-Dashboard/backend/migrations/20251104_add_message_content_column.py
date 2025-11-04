#!/usr/bin/env python3
"""
Add message_content column to guardrail_events table.

This migration adds the missing message_content column that the model expects.
Safe to re-run; skips if column already exists.
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
COLUMN_NAME = 'message_content'


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


def add_column_postgresql(conn, table_name, column_name):
    """Add column to PostgreSQL table"""
    alter_sql = text(f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name} TEXT
    """)
    conn.execute(alter_sql)
    logger.info(f"✅ Added column {column_name} to {table_name}")


def add_column_sqlite(conn, table_name, column_name):
    """Add column to SQLite table"""
    # SQLite doesn't support adding columns with constraints easily
    # We need to use ALTER TABLE ADD COLUMN
    alter_sql = text(f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name} TEXT
    """)
    conn.execute(alter_sql)
    logger.info(f"✅ Added column {column_name} to {table_name}")


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
        
        # Check if column already exists
        if check_column_exists(conn, TABLE_NAME, COLUMN_NAME, database_url):
            logger.info(f"✅ Column {COLUMN_NAME} already exists in {TABLE_NAME}, skipping")
            return
        
        # Add the column
        logger.info(f"Adding column {COLUMN_NAME} to {TABLE_NAME}...")
        
        if 'postgresql' in database_url.lower():
            add_column_postgresql(conn, TABLE_NAME, COLUMN_NAME)
        elif 'sqlite' in database_url.lower():
            add_column_sqlite(conn, TABLE_NAME, COLUMN_NAME)
        else:
            # Generic approach using SQLAlchemy
            try:
                add_column_sqlite(conn, TABLE_NAME, COLUMN_NAME)
            except Exception as e:
                logger.error(f"❌ Failed to add column: {e}")
                raise
        
        logger.info(f"✅ Migration completed successfully")
    
    logger.info("=" * 60)
    logger.info("✅ Migration: Add message_content column - COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception("❌ Migration failed")
        sys.exit(1)
    sys.exit(0)

