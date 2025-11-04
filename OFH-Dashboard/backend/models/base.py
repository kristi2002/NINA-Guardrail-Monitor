#!/usr/bin/env python3
"""
Base Model for SQLAlchemy
Provides common fields and methods for all models
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timezone  # <-- Import timezone

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields and methods"""

    __abstract__ = True

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_dict_serialized(self):
        """Convert model instance to dictionary with serialized datetime fields"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)

    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.updated_at = datetime.now(timezone.utc)  # <-- FIX: Use aware datetime

    @classmethod
    def get_active_records(cls, session):
        """Get all active (non-deleted) records"""
        return session.query(cls).filter(cls.is_deleted.is_(False))

    @classmethod
    def get_by_id(cls, session, record_id):
        """Get a record by ID (active only)"""
        return (
            session.query(cls)
            .filter(cls.id == record_id, cls.is_deleted.is_(False))
            .first()
        )

    def __repr__(self):
        """String representation of the model"""
        return f"<{self.__class__.__name__}(id={self.id})>"
