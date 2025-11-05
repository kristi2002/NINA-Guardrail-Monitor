#!/usr/bin/env python3
"""
Database Initialization Script for Production
Creates database tables and initial data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import init_database, get_database_manager
from models import User
import bcrypt  # type: ignore
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_initial_admin_user():
    """Create initial admin user if it doesn't exist"""
    db_manager = get_database_manager()

    session = db_manager.get_session()
    try:
        # Check if admin user exists
        admin = session.query(User).filter(User.username == "admin").first()

        if not admin:
            logger.info("Creating initial admin user...")

            # Create admin user with hashed password
            password = os.getenv("ADMIN_PASSWORD", "admin123")
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

            admin = User(
                username="admin",
                email="admin@ofh-dashboard.local",
                password_hash=hashed_password.decode("utf-8"),
                role="admin",
                is_active=True,
                is_admin=True,
            )

            session.add(admin)
            session.commit()
            logger.info("✅ Admin user created successfully")
            logger.info(f"   Username: admin")
            logger.info(f"   Password: {password}")
            logger.warning("⚠️  Please change the admin password in production!")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise
    finally:
        session.close()




def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("OFH Dashboard - Database Initialization")
    logger.info("=" * 60)

    try:
        # Get database URL
        database_url = os.getenv("DATABASE_URL", "sqlite:///nina_dashboard.db")
        logger.info(f"Database URL: {database_url}")

        # Initialize database
        logger.info("\nInitializing database...")
        db_manager = init_database(database_url)

        # Test connection
        logger.info("Testing database connection...")
        if not db_manager.test_connection():
            logger.error("❌ Database connection test failed")
            sys.exit(1)

        # Create tables
        logger.info("\nCreating database tables...")
        if not db_manager.create_tables():
            logger.error("❌ Failed to create database tables")
            sys.exit(1)

        # Create initial users
        logger.info("\nCreating initial users...")
        create_initial_admin_user()

        logger.info("\n" + "=" * 60)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 60)

        # Close database connections
        db_manager.close_all_sessions()

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
