#!/usr/bin/env python3
"""
Add category column to guardrail_events table.

This migration adds the category column that the GuardrailEvent model expects.
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
COLUMN_NAME = 'category'


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


def add_column_postgresql(conn, table_name, column_name, default_value=None):
    """Add column to PostgreSQL table with default value"""
    try:
        if default_value:
            # Add column with default value
            alter_sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(30) NOT NULL DEFAULT '{default_value}'")
        else:
            # Add column as nullable
            alter_sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(30)")
        conn.execute(alter_sql)
        conn.commit()
        logger.info(f"✅ Added column {column_name} to {table_name} (PostgreSQL)")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to add column {column_name} to {table_name}: {e}")
        conn.rollback()
        return False


def add_column_sqlite(conn, table_name, column_name):
    """Add column to SQLite table"""
    try:
        alter_sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} VARCHAR(30) DEFAULT 'alert'")
        conn.execute(alter_sql)
        conn.commit()
        logger.info(f"✅ Added column {column_name} to {table_name} (SQLite)")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to add column {column_name} to {table_name}: {e}")
        conn.rollback()
        return False


def update_existing_rows(conn, table_name, database_url):
    """Update existing rows to have a default category value"""
    try:
        # Determine category based on event_type
        update_sql = text(f"""
            UPDATE {table_name} 
            SET category = CASE 
                WHEN event_type LIKE '%conversation%' THEN 'conversation'
                WHEN event_type LIKE '%alarm%' OR event_type LIKE '%warning%' OR event_type LIKE '%violation%' 
                     OR event_type LIKE '%inappropriate%' OR event_type LIKE '%emergency%' THEN 'alert'
                WHEN event_type LIKE '%system%' OR event_type LIKE '%protocol%' OR event_type LIKE '%compliance%' THEN 'system'
                ELSE 'alert'
            END
            WHERE category IS NULL
        """)
        result = conn.execute(update_sql)
        conn.commit()
        rows_updated = result.rowcount
        if rows_updated > 0:
            logger.info(f"✅ Updated {rows_updated} existing rows with category values")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Could not update existing rows: {e}")
        conn.rollback()
        return False


def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    
    logger.info("=" * 60)
    logger.info("Migration: Add category column to guardrail_events")
    logger.info("=" * 60)
    logger.info(f"Database: {database_url}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if column already exists
            if check_column_exists(conn, TABLE_NAME, COLUMN_NAME, database_url):
                logger.info(f"⏭️  Column {COLUMN_NAME} already exists in {TABLE_NAME}, skipping")
                # Still try to update existing rows in case they're null
                update_existing_rows(conn, TABLE_NAME, database_url)
                logger.info("=" * 60)
                logger.info("✅ Migration: Add category column - COMPLETE (column already exists)")
                logger.info("=" * 60)
                return
            
            # Add the column
            logger.info(f"Adding column {COLUMN_NAME} to {TABLE_NAME}...")
            
            is_postgresql = 'postgresql' in database_url.lower()
            
            if is_postgresql:
                success = add_column_postgresql(conn, TABLE_NAME, COLUMN_NAME, default_value='alert')
            else:
                success = add_column_sqlite(conn, TABLE_NAME, COLUMN_NAME)
            
            if success:
                # Update existing rows
                update_existing_rows(conn, TABLE_NAME, database_url)
                logger.info("✅ Migration completed successfully")
            else:
                logger.error("❌ Migration failed")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Migration error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ Migration: Add category column - COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nMigration interrupted by user")
        sys.exit(1)

