#!/usr/bin/env python3
"""
Change Production Passwords Script
Changes default passwords for admin and operator users
"""

import os
import sys
import bcrypt
import getpass
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

def change_user_password(username, new_password=None, interactive=True):
    """Change password for a user"""
    db_manager = get_database_manager()
    
    with db_manager.get_session_context() as session:
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            logger.error(f"❌ User '{username}' not found!")
            return False
        
        # Get password interactively or from argument
        if interactive:
            print(f"\nChanging password for user: {username}")
            new_password = getpass.getpass(f"Enter new password for {username}: ")
            confirm_password = getpass.getpass("Confirm password: ")
            
            if new_password != confirm_password:
                logger.error("❌ Passwords do not match!")
                return False
            
            if len(new_password) < 8:
                logger.warning("⚠️  Password is less than 8 characters. Consider using a stronger password.")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return False
        else:
            if not new_password:
                logger.error("❌ Password required when not in interactive mode")
                return False
        
        # Hash and update password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        user.password_hash = hashed_password
        
        # Reset login attempts and unlock account
        user.login_attempts = 0
        user.locked_until = None
        user.is_active = True
        
        session.commit()
        
        logger.info(f"✅ Password changed successfully for user: {username}")
        return True

def change_all_passwords():
    """Change passwords for admin and operator users"""
    logger.info("=" * 60)
    logger.info("OFH Dashboard - Production Password Changer")
    logger.info("=" * 60)
    logger.info()
    logger.info("This script will change passwords for admin and operator users")
    logger.info("You can skip any user by pressing Enter when prompted")
    logger.info()
    
    # Change admin password
    logger.info("-" * 60)
    response = input("Change admin password? (y/n): ")
    if response.lower() == 'y':
        change_user_password('admin', interactive=True)
    
    # Change operator password
    logger.info("-" * 60)
    response = input("Change operator password? (y/n): ")
    if response.lower() == 'y':
        change_user_password('operator', interactive=True)
    
    logger.info()
    logger.info("=" * 60)
    logger.info("✅ Password changes complete")
    logger.info("=" * 60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Change production passwords')
    parser.add_argument('--admin-password', help='New admin password (not recommended for security)')
    parser.add_argument('--operator-password', help='New operator password (not recommended for security)')
    parser.add_argument('--non-interactive', action='store_true', help='Non-interactive mode (requires --admin-password and --operator-password)')
    
    args = parser.parse_args()
    
    if args.non_interactive:
        if not args.admin_password or not args.operator_password:
            logger.error("❌ Non-interactive mode requires --admin-password and --operator-password")
            return
        
        change_user_password('admin', args.admin_password, interactive=False)
        change_user_password('operator', args.operator_password, interactive=False)
    else:
        change_all_passwords()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

