#!/usr/bin/env python3
"""
Redis Cache Service
Provides caching layer for frequently accessed data
"""

import os
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta
import redis # type: ignore

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        self.enabled = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL', 'memory://')
            
            # Skip Redis if using memory storage
            if redis_url == 'memory://':
                logger.info("Redis caching disabled - using memory storage")
                self.enabled = False
                return
            
            # Parse Redis URL or use individual config
            if redis_url.startswith('redis://'):
                # Full Redis URL
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # Individual config
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', '6379'))
                redis_db = int(os.getenv('REDIS_DB', '0'))
                
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
            
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis cache connected successfully")
            
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.enabled = False
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis: {e}")
            self.enabled = False
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error deleting cache pattern {pattern}: {e}")
            return 0
    
    def clear_cache(self, prefix: str = None) -> int:
        """Clear all cache or cache with specific prefix"""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            if prefix:
                pattern = f"{prefix}:*"
                keys = self.redis_client.keys(pattern)
            else:
                keys = self.redis_client.keys("*")
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value in cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key (in seconds)"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for cache key {key}: {e}")
            return None

# Global cache instance
cache_service = CacheService()

# Convenience functions
def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    return cache_service.get(key)

def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache"""
    return cache_service.set(key, value, ttl)

def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    return cache_service.delete(key)

def clear_cache(prefix: str = None) -> int:
    """Clear cache"""
    return cache_service.clear_cache(prefix)

def cache_exists(key: str) -> bool:
    """Check if key exists"""
    return cache_service.exists(key)

