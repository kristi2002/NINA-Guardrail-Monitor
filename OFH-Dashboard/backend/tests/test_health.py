"""
Health Check Endpoint Tests
"""

import pytest

@pytest.mark.unit
def test_health_endpoint(client):
    """Test health check endpoint returns 200"""
    response = client.get('/api/health')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.get_data(as_text=True)}"
    data = response.get_json()
    assert data is not None, "Response is not JSON"
    assert 'status' in data, f"Missing 'status' in response: {data}"
    assert data['status'] == 'healthy', f"Expected 'healthy', got '{data.get('status')}'"

@pytest.mark.unit
def test_health_endpoint_structure(client):
    """Test health check response structure"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'timestamp' in data
    assert data['status'] == 'healthy'

