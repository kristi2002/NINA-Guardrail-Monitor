"""
Health Check Endpoint Tests
"""

import pytest
from app import app

@pytest.mark.unit
def test_health_endpoint(client):
    """Test health check endpoint returns 200"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

@pytest.mark.unit
def test_health_endpoint_structure(client):
    """Test health check response structure"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'timestamp' in data
    assert data['status'] == 'healthy'

