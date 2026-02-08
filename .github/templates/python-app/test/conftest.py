"""Test configuration and fixtures."""

import pytest
from src.server import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def app_fixture():
    """Create an app instance for testing."""
    app.config['TESTING'] = True
    return app
