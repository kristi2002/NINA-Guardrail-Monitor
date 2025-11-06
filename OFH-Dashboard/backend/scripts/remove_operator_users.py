#!/usr/bin/env python3
"""
Remove Operator Users Script
Removes all users with operator role from the database
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_database_manager
from models import User

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def remove_operator_users():
    """Remove all users with operator role from the database"""
    db_manager = get_database_manager()
    session = db_manager.get_session()
    
    try:
        # Find all users with operator role
        operator_users = session.query(User).filter(
            User.role == 'operator'
        ).all()
        
        if not operator_users:
            logger.info("✅ No operator users found in the database")
            return
        
        logger.info(f"Found {len(operator_users)} operator user(s) to remove:")
        for user in operator_users:
            logger.info(f"  - {user.username} (ID: {user.id}, Email: {user.email})")
        
        # Confirm deletion
        confirm = input(f"\n⚠️  Are you sure you want to delete {len(operator_users)} operator user(s)? (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("❌ Operation cancelled")
            return
        
        # Delete operator users
        deleted_count = 0
        for user in operator_users:
            try:
                session.delete(user)
                deleted_count += 1
                logger.info(f"✅ Deleted operator user: {user.username}")
            except Exception as e:
                logger.error(f"❌ Error deleting user {user.username}: {e}")
        
        # Also check for users with username 'operator' (regardless of role)
        operator_by_username = session.query(User).filter(
            User.username == 'operator'
        ).all()
        
        for user in operator_by_username:
            if user not in operator_users:  # Only if not already deleted
                try:
                    session.delete(user)
                    deleted_count += 1
                    logger.info(f"✅ Deleted user with username 'operator': {user.username}")
                except Exception as e:
                    logger.error(f"❌ Error deleting user {user.username}: {e}")
        
        # Commit changes
        session.commit()
        logger.info(f"\n✅ Successfully removed {deleted_count} operator user(s) from the database")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error removing operator users: {e}")
        raise
    finally:
        session.close()


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("OFH Dashboard - Remove Operator Users")
    logger.info("=" * 60)
    
    try:
        remove_operator_users()
        logger.info("\n" + "=" * 60)
        logger.info("✅ Operation completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

