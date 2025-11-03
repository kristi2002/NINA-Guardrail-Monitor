#!/usr/bin/env python3
"""
Base Service
Provides common functionality for all business logic services
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager
from core.database import get_session_context, get_session

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseService(ABC):
    """Base service class with common business logic patterns"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        return get_session()
    
    @contextmanager
    def get_session_context(self):
        """Get database session with automatic cleanup"""
        if self.db_session:
            yield self.db_session
        else:
            with get_session_context() as session:
                yield session
    
    def log_operation(self, operation: str, user_id: str = None, details: Dict[str, Any] = None):
        """Log business operation"""
        log_data = {
            'operation': operation,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'service': self.__class__.__name__
        }
        if details:
            log_data.update(details)
        
        self.logger.info(f"Business operation: {operation}", extra=log_data)
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate required fields in data dictionary"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        return missing_fields
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
        return sanitized
    
    def format_response(self, success: bool, data: Any = None, message: str = None, errors: List[str] = None) -> Dict[str, Any]:
        """Format service response"""
        response = {
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response['data'] = data
        
        if message:
            response['message'] = message
        
        if errors:
            response['errors'] = errors
        
        return response
    
    def handle_exception(self, e: Exception, operation: str, user_id: str = None) -> Dict[str, Any]:
        """Handle service exceptions"""
        import traceback
        error_trace = traceback.format_exc()
        self.logger.error(f"Error in {operation}: {str(e)}\n{error_trace}", extra={
            'user_id': user_id,
            'operation': operation,
            'error': str(e),
            'service': self.__class__.__name__,
            'traceback': error_trace
        })
        
        return self.format_response(
            success=False,
            message=f"Error in {operation}: {str(e)}",
            errors=[str(e)]
        )
    
    def paginate_results(self, results: List[Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Paginate results"""
        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_results = results[start:end]
        
        return {
            'items': paginated_results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': end < total,
                'has_prev': page > 1
            }
        }
    
    def filter_by_date_range(self, query, date_field, start_date: datetime = None, end_date: datetime = None):
        """Filter query by date range"""
        if start_date:
            query = query.filter(date_field >= start_date)
        if end_date:
            query = query.filter(date_field <= end_date)
        return query
    
    def get_time_range(self, time_range: str) -> tuple[datetime, datetime]:
        """Get start and end datetime for time range string"""
        now = datetime.utcnow()
        
        if time_range == '1h':
            return now - timedelta(hours=1), now
        elif time_range == '24h' or time_range == '1d':
            return now - timedelta(days=1), now
        elif time_range == '7d':
            return now - timedelta(days=7), now
        elif time_range == '30d':
            return now - timedelta(days=30), now
        elif time_range == '90d':
            return now - timedelta(days=90), now
        else:
            # Default to 7 days
            return now - timedelta(days=7), now
    
    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[T]:
        """Get record by ID - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def update(self, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update record - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def delete(self, record_id: int) -> Dict[str, Any]:
        """Delete record - must be implemented by subclasses"""
        pass
