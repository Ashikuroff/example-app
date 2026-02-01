import pytest
from src.server import app

import pytest
from src.server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_hello(client):
    """Test the hello endpoint."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Hello World!' in rv.data


def test_health(client):
    """Test the health check endpoint."""
    rv = client.get('/health')
    assert rv.status_code == 200
    assert b'healthy' in rv.data


def test_metrics(client):
    """Test the metrics endpoint."""
    rv = client.get('/metrics')
    assert rv.status_code == 200


def test_not_found(client):
    """Test 404 error handling."""
    rv = client.get('/nonexistent')
    assert rv.status_code == 404
    assert b'Not found' in rv.data


def test_hello_response_json(client):
    """Test hello endpoint returns valid JSON."""
    rv = client.get('/')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['message'] == 'Hello World!'
    assert 'version' in data
