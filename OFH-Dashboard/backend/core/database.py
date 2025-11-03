#!/usr/bin/env python3
"""
Database Configuration and Setup
Handles database connection, session management, and initialization
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for connection and session handling"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _get_database_url(self):
        """Get database URL from environment or default"""
        return os.getenv('DATABASE_URL', 'sqlite:///nina_dashboard.db')
    
    def _setup_database(self):
        """Setup database engine and session factory"""
        try:
            # Determine if using PostgreSQL or SQLite
            is_postgresql = 'postgresql' in self.database_url
            
            # Configure engine based on database type
            if is_postgresql:
                # PostgreSQL connection pooling for production
                self.engine = create_engine(
                    self.database_url,
                    poolclass=QueuePool,  # Use QueuePool for PostgreSQL
                    pool_pre_ping=True,  # Verify connections before using
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    pool_size=10,  # Number of connections to maintain
                    max_overflow=20,  # Max connections to create beyond pool_size
                    pool_timeout=30,  # Timeout when getting connection from pool
                    echo=False  # Set to True for SQL query logging
                )
                logger.info("✅ PostgreSQL database engine configured with connection pooling")
            else:
                # SQLite configuration for development
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,  # Use StaticPool for SQLite
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
                logger.info("✅ SQLite database engine configured")
            
            # Create session factory
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )
            
            logger.info("✅ Database engine and session factory created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup database: {e}")
            raise
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info("✅ Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            from models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            from models import Base
            Base.metadata.drop_all(bind=self.engine)
            logger.info("✅ Database tables dropped successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to drop database tables: {e}")
            return False
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self):
        """Get database session with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database session error: {e}")
            raise
        finally:
            session.close()
    
    def close_all_sessions(self):
        """Close all database sessions"""
        try:
            self.SessionLocal.remove()
            logger.info("✅ All database sessions closed")
        except Exception as e:
            logger.error(f"❌ Error closing database sessions: {e}")
    
    def get_engine(self):
        """Get database engine"""
        return self.engine

# Global database manager instance
db_manager = None

def init_database(database_url=None):
    """Initialize database manager"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    return db_manager

def get_database_manager():
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = init_database()
    return db_manager

def get_session():
    """Get database session"""
    return get_database_manager().get_session()

@contextmanager
def get_session_context():
    """Get database session with automatic cleanup"""
    with get_database_manager().get_session_context() as session:
        yield session
