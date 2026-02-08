"""
Unit tests for {APP_NAME}
"""
import pytest
from src.server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello(client):
    """Test the hello endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    assert 'message' in response.json

def test_health(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_about(client):
    """Test the about endpoint"""
    response = client.get('/about')
    assert response.status_code == 200
    assert response.json['app'] == '{APP_NAME}'

def test_metrics(client):
    """Test Prometheus metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'app_requests_total' in response.data

def test_not_found(client):
    """Test 404 handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404

def test_request_metrics_tracked(client):
    """Verify request metrics are recorded"""
    response = client.get('/')
    assert response.status_code == 200
    
    # Check metrics contain request tracking
    metrics_response = client.get('/metrics')
    assert b'app_requests_total' in metrics_response.data
    assert b'app_request_duration_seconds' in metrics_response.data
