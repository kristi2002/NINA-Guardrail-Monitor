#!/usr/bin/env python3
"""
Add patient_info column to conversation_sessions table.

This migration adds the patient_info JSON column that the ConversationSession model expects but might not exist in the database.

Safe to re-run; skips if column already exists.
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
COLUMN_NAME = 'patient_info'

def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    logger.info(f"Connecting to DB: {database_url}")
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if column already exists
        if 'postgresql' in database_url.lower():
            # PostgreSQL
            check_column_sql = text(
                f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{TABLE_NAME}' AND column_name = '{COLUMN_NAME}'
                """
            )
        else:
            # SQLite
            # For SQLite, we'll try to add the column and catch the error if it exists
            check_column_sql = None

        if check_column_sql is not None:
            result = conn.execute(check_column_sql).fetchone()
            if result:
                logger.info(f"Column {COLUMN_NAME} already exists in {TABLE_NAME}, skipping migration.")
                return

        logger.info(f"Adding column {COLUMN_NAME} to {TABLE_NAME}...")
        
        # Determine SQL type based on database
        if 'postgresql' in database_url.lower():
            # PostgreSQL uses JSON type
            column_type = 'JSON'
        else:
            # SQLite uses TEXT for JSON
            column_type = 'TEXT'

        alter_sql = text(
            f"""
            ALTER TABLE {TABLE_NAME}
            ADD COLUMN {COLUMN_NAME} {column_type}
            """
        )
        
        try:
            conn.execute(alter_sql)
            logger.info(f"✅ Added column {COLUMN_NAME} to {TABLE_NAME}")
        except Exception as e:
            # If it's a "duplicate column" error, that's fine
            if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info(f"Column {COLUMN_NAME} already exists, skipping.")
            else:
                logger.error(f"Error adding column {COLUMN_NAME}: {e}")
                raise

    logger.info("✅ Migration completed successfully")

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("✅ Migration: Add patient_info column - START")
    logger.info("=" * 60)
    try:
        main()
        logger.info("=" * 60)
        logger.info("✅ Migration: Add patient_info column - COMPLETE")
        logger.info("=" * 60)
    except Exception as e:
        logger.exception("Migration failed")
        sys.exit(1)
    sys.exit(0)

