#!/usr/bin/env python3
"""
Response Serialization Utilities
Provides optimized JSON serialization and response formatting
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from flask import jsonify, Response
import logging

logger = logging.getLogger(__name__)

def serialize_datetime(obj: Any) -> str:
    """Serialize datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def serialize_model(model: Any) -> Dict[str, Any]:
    """Serialize a SQLAlchemy model to dictionary"""
    if hasattr(model, 'to_dict_serialized'):
        return model.to_dict_serialized()
    elif hasattr(model, 'to_dict'):
        return model.to_dict()
    else:
        # Fallback to manual serialization
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name, None)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

def serialize_list(models: List[Any]) -> List[Dict[str, Any]]:
    """Serialize a list of models to dictionaries"""
    return [serialize_model(model) for model in models]

def json_response(data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """
    Create a JSON response with optimized serialization
    
    Args:
        data: Data to serialize (dict, list, model, etc.)
        status_code: HTTP status code
        headers: Optional HTTP headers
    
    Returns:
        Flask Response object
    """
    # Use Flask's jsonify which handles datetime serialization
    # For better performance, could use orjson here
    response = jsonify(data)
    response.status_code = status_code
    
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    
    return response

def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default 200)
        headers: Optional HTTP headers
    
    Returns:
        Flask Response object
    """
    response_data = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response_data['data'] = data
    
    if message:
        response_data['message'] = message
    
    return json_response(response_data, status_code, headers)

def error_response(
    message: str,
    errors: Optional[List[str]] = None,
    status_code: int = 400,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        errors: Optional list of specific errors
        status_code: HTTP status code (default 400)
        error_code: Optional error code for client handling
        headers: Optional HTTP headers
    
    Returns:
        Flask Response object
    """
    response_data = {
        'success': False,
        'error': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if errors:
        response_data['errors'] = errors
    
    if error_code:
        response_data['error_code'] = error_code
    
    return json_response(response_data, status_code, headers)

def paginated_response(
    items: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: Optional[str] = None
) -> Response:
    """
    Create a paginated response
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Optional message
    
    Returns:
        Flask Response object
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    data = {
        'items': serialize_list(items) if items and hasattr(items[0], '__table__') else items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return success_response(data, message)

