#!/usr/bin/env python3
"""
User Model
Handles user authentication and authorization
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Index
from .base import BaseModel
import bcrypt
from datetime import datetime, timedelta, timezone  # <-- Import timezone
import jwt
import os


class User(BaseModel):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    # Basic user information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # User details
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)

    # Status and permissions
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    role = Column(
        String(20), default="operator", nullable=False
    )  # admin, operator, viewer

    # Authentication tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Profile information
    department = Column(String(50), nullable=True)
    position = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    # alerts = relationship("Alert", back_populates="assigned_user")
    # audit_logs = relationship("AuditLog", back_populates="user")

    # Indexes
    __table_args__ = (
        Index("idx_user_username", "username"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
        Index("idx_user_active", "is_active"),
    )

    def set_password(self, password):
        """Hash and set password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def generate_token(self, expires_in=86400):
        """Generate JWT token for user"""
        payload = {
            "user_id": self.id,
            "username": self.username,
            "role": self.role,
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=expires_in),  # <-- FIX: Use aware datetime
        }
        secret_key = os.getenv("SECRET_KEY", "nina-guardrail-monitor-secret-key")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    def is_locked(self):
        """Check if user account is locked"""
        if self.locked_until is None:
            return False
        # <-- FIX: Use aware datetime for comparison
        return datetime.now(timezone.utc) < self.locked_until

    def lock_account(self, minutes=30):
        """Lock user account for specified minutes"""
        # <-- FIX: Use aware datetime
        self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.login_attempts = 0  # Reset attempts *after* locking

    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.login_attempts = 0

    def record_login_attempt(self, success=False):
        """Record login attempt"""
        if success:
            self.login_attempts = 0
            self.last_login = datetime.now(timezone.utc)  # <-- FIX: Use aware datetime
            self.locked_until = None  # Ensure account is unlocked on success
        else:
            self.login_attempts += 1
            if self.login_attempts >= 5:  # Lock after 5 failed attempts
                self.lock_account()

    def to_dict_safe(self):
        """Convert to dictionary excluding sensitive information"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "role": self.role,
            "last_login": (
                self.last_login.isoformat() if self.last_login is not None else None
            ),
            "department": self.department,
            "position": self.position,
            "created_at": (
                self.created_at.isoformat() if self.created_at is not None else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at is not None else None
            ),
        }

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
