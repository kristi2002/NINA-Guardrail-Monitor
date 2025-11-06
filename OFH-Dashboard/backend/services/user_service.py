#!/usr/bin/env python3
"""
User Service
Handles business logic for user management and authentication
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime, timedelta
from .base_service import BaseService
from repositories.user_repository import UserRepository
from models.user import User
import logging
import bcrypt # type: ignore
import jwt # type: ignore
import os

logger = logging.getLogger(__name__)

class UserService(BaseService):
    """Service for user business logic"""
    
    def __init__(self, db_session: Optional[Session] = None):
        super().__init__(db_session)
        self.user_repo = UserRepository(self.get_session())
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.user_repo.get_by_id(user_id)
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return self.user_repo.get_by_username(username)
        except Exception as e:
            self.logger.error(f"Error getting user {username}: {e}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return self.user_repo.get_by_email(email)
        except Exception as e:
            self.logger.error(f"Error getting user {email}: {e}")
            return None
    
    def get_all_users(self, limit: int = 100) -> List[User]:
        """Get all users"""
        try:
            return self.user_repo.get_all(limit=limit)
        except Exception as e:
            self.logger.error(f"Error getting all users: {e}")
            return []
    
    def get_active_users(self, limit: int = 100) -> List[User]:
        """Get active users"""
        try:
            return self.user_repo.get_by_filters({'is_active': True}, limit=limit)
        except Exception as e:
            self.logger.error(f"Error getting active users: {e}")
            return []
    
    def get_users_by_role(self, role: str, limit: int = 100) -> List[User]:
        """Get users by role"""
        try:
            return self.user_repo.get_by_filters({'role': role}, limit=limit)
        except Exception as e:
            self.logger.error(f"Error getting users by role {role}: {e}")
            return []
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password']
            missing_fields = self.validate_required_fields(data, required_fields)
            
            if missing_fields:
                return self.format_response(
                    success=False,
                    message="Missing required fields",
                    errors=[f"Missing field: {field}" for field in missing_fields]
                )
            
            # Sanitize input
            sanitized_data = self.sanitize_input(data)
            
            # Check if username already exists
            if self.user_repo.get_by_username(sanitized_data['username']):
                return self.format_response(
                    success=False,
                    message="Username already exists"
                )
            
            # Check if email already exists
            if self.user_repo.get_by_email(sanitized_data['email']):
                return self.format_response(
                    success=False,
                    message="Email already exists"
                )
            
            # Hash password
            password = sanitized_data.pop('password')
            
            # Set default values
            sanitized_data.setdefault('is_active', True)
            sanitized_data.setdefault('is_admin', False)
            sanitized_data.setdefault('role', 'admin')
            sanitized_data.setdefault('login_attempts', 0)
            
            # Create user
            user = self.user_repo.create(**sanitized_data)
            
            # Set password after creation
            user.set_password(password)
            self.user_repo.update(user.id, password_hash=user.password_hash)
            
            self.log_operation('user_created', details={
                'username': user.username,
                'email': user.email,
                'role': user.role
            })
            
            return self.format_response(
                success=True,
                data=user.to_dict_safe(),
                message="User created successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'create_user')
    
    def update(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        try:
            # Sanitize input
            sanitized_data = self.sanitize_input(data)
            
            # Handle password update separately
            if 'password' in sanitized_data:
                password = sanitized_data.pop('password')
                user = self.user_repo.get_by_id(user_id)
                if user:
                    user.set_password(password)
                    sanitized_data['password_hash'] = user.password_hash
            
            # Update user
            user = self.user_repo.update(user_id, **sanitized_data)
            
            if not user:
                return self.format_response(
                    success=False,
                    message="User not found"
                )
            
            self.log_operation('user_updated', details={
                'user_id': user_id,
                'updated_fields': list(sanitized_data.keys())
            })
            
            return self.format_response(
                success=True,
                data=user.to_dict_safe(),
                message="User updated successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'update_user')
    
    def delete(self, user_id: int) -> Dict[str, Any]:
        """Delete user (soft delete)"""
        try:
            success = self.user_repo.soft_delete(user_id)
            
            if not success:
                return self.format_response(
                    success=False,
                    message="User not found"
                )
            
            self.log_operation('user_deleted', details={'user_id': user_id})
            
            return self.format_response(
                success=True,
                message="User deleted successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'delete_user')
    
    def delete_users_by_role(self, role: str) -> Dict[str, Any]:
        """Delete all users with a specific role (hard delete)"""
        try:
            # Get all users with this role, including soft-deleted ones
            # We need to query directly to bypass soft-delete filter
            from models.user import User
            session = self.get_session()
            users = session.query(User).filter(User.role == role).all()
            
            if not users:
                return self.format_response(
                    success=True,
                    message=f"No users with role '{role}' found",
                    data={'deleted_count': 0}
                )
            
            deleted_count = 0
            for user in users:
                try:
                    self.user_repo.hard_delete(user.id)  # Hard delete
                    deleted_count += 1
                    self.logger.info(f"Deleted user {user.username} (role: {role})")
                except Exception as e:
                    self.logger.error(f"Error deleting user {user.username}: {e}")
            
            # Also check for users with username matching the role
            user_by_username = self.user_repo.get_by_username(role)
            if user_by_username and user_by_username not in users:
                try:
                    self.user_repo.hard_delete(user_by_username.id)
                    deleted_count += 1
                    self.logger.info(f"Deleted user with username '{role}'")
                except Exception as e:
                    self.logger.error(f"Error deleting user with username '{role}': {e}")
            
            self.log_operation('users_deleted_by_role', details={'role': role, 'count': deleted_count})
            
            return self.format_response(
                success=True,
                message=f"Deleted {deleted_count} user(s) with role '{role}'",
                data={'deleted_count': deleted_count}
            )
            
        except Exception as e:
            return self.handle_exception(e, 'delete_users_by_role')
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with username and password"""
        try:
            user = self.user_repo.get_by_username(username)
            
            if not user:
                self.logger.warning(f"Login attempt for non-existent user: {username}")
                return self.format_response(
                    success=False,
                    message="Username not found"
                )
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Login attempt for inactive user: {username}")
                return self.format_response(
                    success=False,
                    message="Account is deactivated"
                )
            
            # Check if account is locked
            if user.is_locked():
                self.logger.warning(f"Login attempt for locked account: {username}")
                return self.format_response(
                    success=False,
                    message="Account is locked due to too many failed login attempts"
                )
            
            # Check password
            try:
                password_valid = user.check_password(password)
            except Exception as password_error:
                self.logger.error(f"Error checking password for user {username}: {password_error}", exc_info=True)
                return self.format_response(
                    success=False,
                    message="Error validating password"
                )
            
            if not password_valid:
                # Record failed login attempt
                user.record_login_attempt(success=False)
                try:
                    self.user_repo.update(user.id,
                        login_attempts=user.login_attempts,
                        locked_until=user.locked_until
                    )
                except Exception as update_error:
                    self.logger.error(f"Error updating login attempts for user {username}: {update_error}", exc_info=True)
                
                # Provide specific password error message
                remaining_attempts = 5 - user.login_attempts
                if remaining_attempts > 0:
                    message = f"Password is incorrect. {remaining_attempts} attempt(s) remaining."
                else:
                    message = "Password is incorrect. Account has been locked due to too many failed attempts."
                
                self.logger.warning(f"Invalid password for user: {username}, {remaining_attempts} attempts remaining")
                return self.format_response(
                    success=False,
                    message=message
                )
            
            # Record successful login
            user.record_login_attempt(success=True)
            try:
                self.user_repo.update(user.id,
                    login_attempts=user.login_attempts,
                    last_login=user.last_login,
                    locked_until=user.locked_until
                )
            except Exception as update_error:
                self.logger.error(f"Error updating successful login for user {username}: {update_error}", exc_info=True)
            
            # Generate token
            try:
                token = user.generate_token()
            except Exception as token_error:
                self.logger.error(f"Error generating token for user {username}: {token_error}", exc_info=True)
                return self.format_response(
                    success=False,
                    message="Error generating authentication token"
                )
            
            self.log_operation('user_authenticated', user.username, {
                'user_id': user.id,
                'role': user.role
            })
            
            return self.format_response(
                success=True,
                data={
                    'user': user.to_dict_safe(),
                    'token': token
                },
                message="Authentication successful"
            )
            
        except Exception as e:
            self.logger.error(f"Exception in authenticate_user for username '{username}': {str(e)}", exc_info=True)
            return self.format_response(
                success=False,
                message=f"Authentication error: {str(e)}",
                errors=[str(e)]
            )
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token"""
        try:
            secret_key = os.getenv('SECRET_KEY', 'nina-guardrail-monitor-secret-key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            user = self.user_repo.get_by_id(payload['user_id'])
            
            if not user or not user.is_active:
                return self.format_response(
                    success=False,
                    message="Invalid token"
                )
            
            return self.format_response(
                success=True,
                data=user.to_dict_safe(),
                message="Token is valid"
            )
            
        except jwt.ExpiredSignatureError:
            return self.format_response(
                success=False,
                message="Token has expired"
            )
        except jwt.InvalidTokenError:
            return self.format_response(
                success=False,
                message="Invalid token"
            )
        except Exception as e:
            return self.handle_exception(e, 'validate_token')
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                return self.format_response(
                    success=False,
                    message="User not found"
                )
            
            # Verify current password
            if not user.check_password(current_password):
                return self.format_response(
                    success=False,
                    message="Current password is incorrect"
                )
            
            # Set new password
            user.set_password(new_password)
            self.user_repo.update(user.id, password_hash=user.password_hash)
            
            self.log_operation('password_changed', user.username, {
                'user_id': user_id
            })
            
            return self.format_response(
                success=True,
                message="Password changed successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'change_password')
    
    def reset_password(self, email: str) -> Dict[str, Any]:
        """Reset user password (send reset email)"""
        try:
            user = self.user_repo.get_by_email(email)
            
            if not user:
                # Don't reveal if email exists or not
                return self.format_response(
                    success=True,
                    message="If the email exists, a password reset link has been sent"
                )
            
            # Generate reset token
            reset_token = jwt.encode({
                'user_id': user.id,
                'email': user.email,
                'exp': datetime.utcnow() + timedelta(hours=1)
            }, os.getenv('SECRET_KEY', 'nina-guardrail-monitor-secret-key'), algorithm='HS256')
            
            # Send email with reset token if email is configured
            from core.config_helper import ConfigHelper
            email_config = ConfigHelper.get_email_config()
            
            if email_config['enabled'] and email_config['smtp_user']:
                # TODO: Implement actual email sending service
                # For now, log the token (email service integration needed)
                self.logger.info(f"Password reset token for {email}: {reset_token}")
                self.logger.info(f"Email service configured. Token should be sent to {email}")
            else:
                self.logger.warning(f"Email service not configured. Password reset token generated but not sent: {reset_token}")
            
            self.log_operation('password_reset_requested', user.username, {
                'user_id': user.id,
                'email': email
            })
            
            return self.format_response(
                success=True,
                message="If the email exists, a password reset link has been sent"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'reset_password')
    
    def lock_user(self, user_id: int, minutes: int = 30) -> Dict[str, Any]:
        """Lock user account"""
        try:
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                return self.format_response(
                    success=False,
                    message="User not found"
                )
            
            user.lock_account(minutes)
            self.user_repo.update(user.id,
                locked_until=user.locked_until,
                login_attempts=user.login_attempts
            )
            
            self.log_operation('user_locked', details={
                'user_id': user_id,
                'locked_until': user.locked_until.isoformat(),
                'minutes': minutes
            })
            
            return self.format_response(
                success=True,
                message=f"User account locked for {minutes} minutes"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'lock_user')
    
    def unlock_user(self, user_id: int) -> Dict[str, Any]:
        """Unlock user account"""
        try:
            user = self.user_repo.get_by_id(user_id)
            
            if not user:
                return self.format_response(
                    success=False,
                    message="User not found"
                )
            
            user.unlock_account()
            self.user_repo.update(user.id,
                locked_until=user.locked_until,
                login_attempts=user.login_attempts
            )
            
            self.log_operation('user_unlocked', details={'user_id': user_id})
            
            return self.format_response(
                success=True,
                message="User account unlocked"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'unlock_user')
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            stats = self.user_repo.get_user_statistics()
            
            self.log_operation('user_statistics_requested')
            
            return self.format_response(
                success=True,
                data=stats,
                message="User statistics retrieved successfully"
            )
            
        except Exception as e:
            return self.handle_exception(e, 'get_user_statistics')
