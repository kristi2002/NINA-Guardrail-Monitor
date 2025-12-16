"""
Pytest configuration and fixtures for OFH Dashboard Backend tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['FLASK_DEBUG'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-not-for-production'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing-only-not-for-production'
os.environ['CORS_ORIGINS'] = 'http://localhost:3001'
os.environ['REDIS_URL'] = 'memory://'

@pytest.fixture
def app():
    """Create Flask application for testing"""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def reset_db(app):
    """Reset database before each test"""
    try:
        from core.database import get_database_manager
        db_manager = get_database_manager()
        if db_manager:
            db_manager.drop_tables()
            db_manager.create_tables()
        yield
        # Cleanup after test
        if db_manager:
            db_manager.drop_tables()
    except Exception:
        # If database operations fail, continue anyway (for tests that don't need DB)
        yield

