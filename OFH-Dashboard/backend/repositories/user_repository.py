#!/usr/bin/env python3
"""
User Repository
Handles user-specific database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from .base_repository import BaseRepository
from models.user import User
import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    """Repository for User model with user-specific operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.get_by_field('username', username)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.get_by_field('email', email)
    
    def get_active_users(self, limit: int = 100) -> List[User]:
        """Get active users"""
        try:
            return self.db.query(User).filter(
                User.is_active == True,
                User.is_deleted.is_(False)
            ).order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    def get_users_by_role(self, role: str, limit: int = 100) -> List[User]:
        """Get users by role"""
        try:
            return self.db.query(User).filter(
                User.role == role,
                User.is_deleted.is_(False)
            ).order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            raise
    
    def get_locked_users(self, limit: int = 100) -> List[User]:
        """Get locked users"""
        try:
            return self.db.query(User).filter(
                User.locked_until.isnot(None),
                User.locked_until > datetime.utcnow(),
                User.is_deleted.is_(False)
            ).order_by(desc(User.locked_until)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting locked users: {e}")
            raise
    
    def get_recent_logins(self, hours: int = 24, limit: int = 100) -> List[User]:
        """Get users with recent logins"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            return self.db.query(User).filter(
                User.last_login >= cutoff_time,
                User.is_deleted.is_(False)
            ).order_by(desc(User.last_login)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent logins: {e}")
            raise
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            # Total users
            total_users = self.db.query(User).filter(User.is_deleted.is_(False)).count()
            
            # Active users
            active_users = self.db.query(User).filter(
                User.is_active == True,
                User.is_deleted.is_(False)
            ).count()
            
            # Locked users
            locked_users = self.db.query(User).filter(
                User.locked_until.isnot(None),
                User.locked_until > datetime.utcnow(),
                User.is_deleted.is_(False)
            ).count()
            
            # Users by role
            role_stats = self.db.query(
                User.role,
                func.count(User.id).label('count')
            ).filter(User.is_deleted.is_(False)).group_by(User.role).all()
            
            # Users by department
            department_stats = self.db.query(
                User.department,
                func.count(User.id).label('count')
            ).filter(
                User.is_deleted.is_(False),
                User.department.isnot(None)
            ).group_by(User.department).all()
            
            # Recent logins (last 24 hours)
            recent_logins = self.db.query(User).filter(
                User.last_login >= datetime.utcnow() - timedelta(hours=24),
                User.is_deleted.is_(False)
            ).count()
            
            # Calculate rates
            active_user_rate = (active_users / total_users) if total_users > 0 else 0
            locked_user_rate = (locked_users / total_users) if total_users > 0 else 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'locked_users': locked_users,
                'recent_logins_24h': recent_logins,
                'active_user_rate': active_user_rate,
                'locked_user_rate': locked_user_rate,
                'role_distribution': {stat.role: stat.count for stat in role_stats},
                'department_distribution': {stat.department: stat.count for stat in department_stats},
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            raise
    
    def get_user_activity_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get user activity metrics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Recent logins
            recent_logins = self.db.query(User).filter(
                User.last_login >= cutoff_time,
                User.is_deleted.is_(False)
            ).count()
            
            # Users with high activity (multiple logins)
            high_activity_users = self.db.query(User).filter(
                User.last_login >= cutoff_time,
                User.is_deleted.is_(False)
            ).count()  # This would need more sophisticated logic
            
            # Failed login attempts
            failed_attempts = self.db.query(User).filter(
                User.login_attempts > 0,
                User.is_deleted.is_(False)
            ).count()
            
            # Calculate rates
            total_users = self.db.query(User).filter(User.is_deleted.is_(False)).count()
            activity_rate = (recent_logins / total_users) if total_users > 0 else 0
            failed_login_rate = (failed_attempts / total_users) if total_users > 0 else 0
            
            return {
                'recent_logins': recent_logins,
                'high_activity_users': high_activity_users,
                'failed_login_attempts': failed_attempts,
                'activity_rate': activity_rate,
                'failed_login_rate': failed_login_rate,
                'time_range_hours': hours,
                'generated_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting user activity metrics: {e}")
            raise
    
    def search_users(self, search_term: str, limit: int = 50) -> List[User]:
        """Search users by name, username, or email"""
        try:
            search_conditions = [
                User.username.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%"),
                User.first_name.ilike(f"%{search_term}%"),
                User.last_name.ilike(f"%{search_term}%")
            ]
            
            return self.db.query(User).filter(
                or_(*search_conditions),
                User.is_deleted.is_(False)
            ).order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            raise
    
    def get_users_by_department(self, department: str, limit: int = 100) -> List[User]:
        """Get users by department"""
        try:
            return self.db.query(User).filter(
                User.department == department,
                User.is_deleted.is_(False)
            ).order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting users by department {department}: {e}")
            raise
    
    def get_users_requiring_attention(self, limit: int = 100) -> List[User]:
        """Get users requiring attention (locked, high failed attempts, etc.)"""
        try:
            return self.db.query(User).filter(
                User.is_deleted.is_(False),
                or_(
                    User.locked_until.isnot(None),
                    User.login_attempts >= 3,
                    User.is_active == False
                )
            ).order_by(desc(User.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting users requiring attention: {e}")
            raise
