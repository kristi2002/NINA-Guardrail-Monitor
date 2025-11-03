#!/usr/bin/env python3
"""
Query Optimization Utilities
Provides helpers for optimized database queries
"""

from typing import List, Optional, Any
from sqlalchemy.orm import Query, joinedload, selectinload, subqueryload
from sqlalchemy import func, desc, asc
import logging

logger = logging.getLogger(__name__)

def optimize_query(
    query: Query,
    eager_loads: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: Optional[str] = None,
    order_desc: bool = True
) -> Query:
    """
    Optimize a SQLAlchemy query with eager loading and pagination
    
    Args:
        query: SQLAlchemy query object
        eager_loads: List of relationships to eager load (using joinedload)
        limit: Maximum number of results
        offset: Number of results to skip
        order_by: Column name to order by
        order_desc: If True, order descending; otherwise ascending
    
    Returns:
        Optimized query object
    """
    # Add eager loading for relationships
    if eager_loads:
        for relationship in eager_loads:
            try:
                # Try joinedload first (most efficient for 1-to-many)
                query = query.options(joinedload(relationship))
            except Exception:
                try:
                    # Fallback to selectinload (better for many-to-many)
                    query = query.options(selectinload(relationship))
                except Exception as e:
                    logger.warning(f"Could not eager load relationship '{relationship}': {e}")
    
    # Add ordering
    if order_by:
        try:
            column = getattr(query.column_descriptions[0]['entity'], order_by, None)
            if column:
                if order_desc:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        except Exception as e:
            logger.warning(f"Could not order by '{order_by}': {e}")
    
    # Add pagination
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    return query

def count_efficiently(query: Query) -> int:
    """
    Count query results efficiently using COUNT(*)
    
    Args:
        query: SQLAlchemy query object
    
    Returns:
        Number of results
    """
    # Use COUNT(*) which is more efficient than loading all records
    count_query = query.statement.with_only_columns(func.count()).order_by(None)
    return query.session.execute(count_query).scalar() or 0

def batch_fetch(
    query: Query,
    batch_size: int = 100,
    limit: Optional[int] = None
):
    """
    Fetch results in batches to avoid loading all records into memory
    
    Args:
        query: SQLAlchemy query object
        batch_size: Number of records per batch
        limit: Maximum total number of records to fetch
    
    Yields:
        Batches of results
    """
    offset = 0
    fetched = 0
    
    while True:
        batch_query = query.offset(offset).limit(batch_size)
        batch = batch_query.all()
        
        if not batch:
            break
        
        yield batch
        fetched += len(batch)
        offset += batch_size
        
        if limit and fetched >= limit:
            break

def apply_filters(
    query: Query,
    filters: dict,
    filter_mapping: Optional[dict] = None
) -> Query:
    """
    Apply multiple filters to a query
    
    Args:
        query: SQLAlchemy query object
        filters: Dictionary of filter criteria
        filter_mapping: Optional mapping of filter keys to model attributes
    
    Returns:
        Query with filters applied
    """
    model = query.column_descriptions[0]['entity']
    
    for key, value in filters.items():
        if value is None:
            continue
        
        # Use mapping if provided, otherwise use key directly
        attr_name = filter_mapping.get(key, key) if filter_mapping else key
        
        try:
            attr = getattr(model, attr_name, None)
            if attr is None:
                logger.warning(f"Filter attribute '{attr_name}' not found on model")
                continue
            
            # Apply appropriate filter based on value type
            if isinstance(value, list):
                query = query.filter(attr.in_(value))
            elif isinstance(value, dict):
                # Support range queries like {'gte': 10, 'lte': 20}
                if 'gte' in value:
                    query = query.filter(attr >= value['gte'])
                if 'lte' in value:
                    query = query.filter(attr <= value['lte'])
                if 'gt' in value:
                    query = query.filter(attr > value['gt'])
                if 'lt' in value:
                    query = query.filter(attr < value['lt'])
            else:
                query = query.filter(attr == value)
        except Exception as e:
            logger.warning(f"Could not apply filter '{key}': {e}")
    
    return query

