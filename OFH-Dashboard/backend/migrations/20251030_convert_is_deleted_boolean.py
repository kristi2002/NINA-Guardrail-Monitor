#!/usr/bin/env python3
"""
Convert is_deleted columns from integer to boolean across all tables that inherit BaseModel.

Maps: 0 -> FALSE, 1 -> TRUE
Safe to re-run; skips if already boolean.
"""

import os
import logging
import sys
from sqlalchemy import create_engine, text


logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)


TABLES = [
    'alerts',
    'conversation_sessions',
    'guardrail_events',
    'users',
    'chat_messages',
    'operator_actions',
]


def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    logger.info(f"Connecting to DB: {database_url}")
    engine = create_engine(database_url)

    with engine.begin() as conn:
        for table in TABLES:
            logger.info(f"Processing table: {table}")

            # Detect current data type of is_deleted
            dtype_sql = text(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = 'is_deleted'
                """
            )
            result = conn.execute(dtype_sql, {"table": table}).fetchone()
            if not result:
                logger.info(f" - Column is_deleted not found on {table}, skipping")
                continue

            current_type = result[0]
            logger.info(f" - Current type: {current_type}")
            if current_type == 'boolean':
                logger.info(" - Already boolean, skipping")
                continue

            # Convert integer->boolean mapping 0->FALSE, 1->TRUE
            logger.info(" - Converting to boolean (0->FALSE, 1->TRUE)")
            alter_sql = text(
                f"""
                ALTER TABLE {table}
                ALTER COLUMN is_deleted TYPE boolean USING (is_deleted = 1)
                """
            )
            conn.execute(alter_sql)
            logger.info(" - Conversion complete")

    logger.info("All conversions processed successfully")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception("Migration failed")
        sys.exit(1)
    sys.exit(0)


