"""Unit tests for the Flask server."""

import pytest
import json
from src.server import app


def test_hello(client):
    """Test the hello endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'version' in data


def test_health(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_metrics(client):
    """Test the metrics endpoint."""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'prometheus' in response.data.lower() or b'app_requests_total' in response.data


def test_404(client):
    """Test 404 handling."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == 'Not found'


def test_request_metrics(client):
    """Test that request metrics are being recorded."""
    # Make a request
    response = client.get('/')
    assert response.status_code == 200
    
    # Check metrics
    metrics_response = client.get('/metrics')
    assert b'app_requests_total' in metrics_response.data
    assert b'app_request_duration_seconds' in metrics_response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
