#!/usr/bin/env python3
"""
Reset admin password script
Resets the admin user password to a known value
"""

import os
import sys
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_database_manager
from models.user import User
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_admin_password():
    """Reset admin password"""
    db_manager = get_database_manager()
    
    with db_manager.get_session_context() as session:
        # Get admin user
        admin = session.query(User).filter(User.username == 'admin').first()
        
        if not admin:
            logger.error("❌ Admin user not found!")
            logger.info("Run init_database.py first to create users")
            return False
        
        # Get password from env or use default
        new_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        # Hash and update password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        admin.password_hash = hashed_password
        
        # Reset login attempts and unlock account
        admin.login_attempts = 0
        admin.locked_until = None
        admin.is_active = True
        
        session.commit()
        
        logger.info("✅ Admin password reset successfully")
        logger.info(f"   Username: admin")
        logger.info(f"   Password: {new_password}")
        logger.info("   Account unlocked and active")
        
        return True

if __name__ == '__main__':
    try:
        reset_admin_password()
    except Exception as e:
        logger.error(f"❌ Failed to reset password: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

