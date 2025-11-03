#!/usr/bin/env python3
"""
Reset database schema to match current SQLAlchemy models:
 - Drops all tables
 - Recreates all tables
 - Re-initializes seed users via init_database.py logic

Use for development when prior schemas diverge from models.
"""

import os
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    database_url = os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    logger.info("=========================================")
    logger.info("OFH Dashboard - Database Reset (DEV)")
    logger.info("=========================================")
    logger.info(f"Database URL: {database_url}")

    db = init_database(database_url)

    logger.info("Dropping all tables...")
    if not db.drop_tables():
        raise RuntimeError("Failed to drop tables")

    logger.info("Creating all tables...")
    if not db.create_tables():
        raise RuntimeError("Failed to create tables")

    # Reuse existing initialization to seed users
    try:
        # Import from parent directory
        from init_database import create_initial_admin_user, create_initial_operator_user
        logger.info("Seeding initial users...")
        create_initial_admin_user()
        create_initial_operator_user()
    except Exception as e:
        logger.warning(f"Seeding users failed or unavailable: {e}")

    db.close_all_sessions()
    logger.info("✅ Database reset completed")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.exception("Database reset failed")
        sys.exit(1)
    sys.exit(0)


