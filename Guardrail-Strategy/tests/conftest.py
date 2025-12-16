"""
Pytest configuration and fixtures for Guardrail-Strategy tests
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
os.environ['PORT'] = '5001'
os.environ['LOG_LEVEL'] = 'DEBUG'

@pytest.fixture
def app():
    """Create Flask application for testing"""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

