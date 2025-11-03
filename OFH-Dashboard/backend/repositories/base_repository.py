#!/usr/bin/env python3
"""
Base Repository
Provides common CRUD operations for all repositories
"""

from typing import List, Optional, Type, TypeVar, Dict, Any
from sqlalchemy.orm import Session # type: ignore
from sqlalchemy import and_, or_, desc, asc # type: ignore
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            logger.debug(f"Created {self.model.__name__}: {instance.id}")
            return instance
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """Get record by ID"""
        try:
            query = self.db.query(self.model).filter(self.model.id == record_id)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            return query.first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by ID {record_id}: {e}")
            raise
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Get record by field value"""
        try:
            field = getattr(self.model, field_name)
            query = self.db.query(self.model).filter(field == value)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            return query.first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {e}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100, order_by: str = 'id') -> List[T]:
        """Get all records with pagination"""
        try:
            order_field = getattr(self.model, order_by, self.model.id)
            query = self.db.query(self.model)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            return query.order_by(order_field).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise
    
    def get_by_filters(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[T]:
        """Get records by multiple filters"""
        try:
            query = self.db.query(self.model)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(value, list):
                        query = query.filter(field.in_(value))
                    else:
                        query = query.filter(field == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by filters: {e}")
            raise
    
    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """Update record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            instance.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(instance)
            logger.debug(f"Updated {self.model.__name__}: {record_id}")
            return instance
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} {record_id}: {e}")
            raise
    
    def soft_delete(self, record_id: int) -> bool:
        """Soft delete record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if not instance:
                return False
            
            instance.soft_delete()
            self.db.commit()
            logger.debug(f"Soft deleted {self.model.__name__}: {record_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error soft deleting {self.model.__name__} {record_id}: {e}")
            raise
    
    def hard_delete(self, record_id: int) -> bool:
        """Hard delete record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if not instance:
                return False
            
            self.db.delete(instance)
            self.db.commit()
            logger.debug(f"Hard deleted {self.model.__name__}: {record_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error hard deleting {self.model.__name__} {record_id}: {e}")
            raise
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Count records with optional filters"""
        try:
            query = self.db.query(self.model)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        if isinstance(value, list):
                            query = query.filter(field.in_(value))
                        else:
                            query = query.filter(field == value)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    def exists(self, record_id: int) -> bool:
        """Check if record exists"""
        try:
            query = self.db.query(self.model).filter(self.model.id == record_id)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            return query.first() is not None
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} {record_id}: {e}")
            raise
    
    def search(self, search_term: str, search_fields: List[str], skip: int = 0, limit: int = 100) -> List[T]:
        """Search records by term in specified fields"""
        try:
            query = self.db.query(self.model)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            
            search_conditions = []
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {e}")
            raise
    
    def get_recent(self, days: int = 7, limit: int = 100) -> List[T]:
        """Get recent records from the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.db.query(self.model).filter(self.model.created_at >= cutoff_date)
            if hasattr(self.model, 'is_deleted'):
                query = query.filter(self.model.is_deleted.is_(False))
            return query.order_by(desc(self.model.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent {self.model.__name__}: {e}")
            raise
