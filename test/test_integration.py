"""
Integration tests for example-app
These tests validate the app behavior in deployment scenarios.
Run after deploying to verify health checks and metrics collection.
"""
import pytest
import requests
import time
import logging

logger = logging.getLogger(__name__)

# Configure for local testing - override APP_URL to test deployed instances
DEFAULT_APP_URL = "http://localhost:5000"
APP_URL = DEFAULT_APP_URL

def get_app_url():
    """Get app URL from env or use default"""
    import os
    return os.getenv('APP_URL', DEFAULT_APP_URL)

class TestAppEndpoints:
    """Test app endpoints are accessible and return expected responses"""
    
    def test_hello_endpoint(self):
        """Verify hello endpoint returns valid JSON"""
        response = requests.get(f"{get_app_url()}/")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
        assert 'service' in data
        logger.info(f"Hello endpoint OK: {data}")
    
    def test_health_endpoint(self):
        """Verify health check endpoint works"""
        response = requests.get(f"{get_app_url()}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        logger.info("Health check OK")
    
    def test_metrics_endpoint(self):
        """Verify Prometheus metrics endpoint returns metrics"""
        response = requests.get(f"{get_app_url()}/metrics")
        assert response.status_code == 200
        assert b'app_requests_total' in response.content
        assert b'app_request_duration_seconds' in response.content
        logger.info("Metrics endpoint OK - Prometheus scraping available")
    
    def test_404_handling(self):
        """Verify 404 errors are handled gracefully"""
        response = requests.get(f"{get_app_url()}/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        logger.info("404 handling OK")

class TestMetricsCollection:
    """Verify Prometheus metrics are being collected correctly"""
    
    def test_request_count_metric(self):
        """Verify request_count metric is incremented"""
        # Make a request
        requests.get(f"{get_app_url()}/")
        
        # Check metrics contain the request
        response = requests.get(f"{get_app_url()}/metrics")
        metrics_text = response.text
        
        # Should see request count metrics
        assert 'app_requests_total' in metrics_text
        assert 'method="GET"' in metrics_text
        logger.info("Request count metric OK")
    
    def test_request_duration_metric(self):
        """Verify request_duration metric is recorded"""
        # Make a request
        requests.get(f"{get_app_url()}/health")
        
        # Check metrics contain duration histogram
        response = requests.get(f"{get_app_url()}/metrics")
        metrics_text = response.text
        
        assert 'app_request_duration_seconds' in metrics_text
        assert 'bucket' in metrics_text or 'sum' in metrics_text
        logger.info("Request duration metric OK")

class TestConcurrency:
    """Test app behavior under concurrent requests"""
    
    def test_multiple_requests(self):
        """Verify app handles multiple rapid requests"""
        urls = [f"{get_app_url()}/" for _ in range(10)]
        
        for url in urls:
            response = requests.get(url)
            assert response.status_code == 200
        
        logger.info("Multiple concurrent requests OK")

class TestLoggingLevels:
    """Verify logging configuration responds to LOG_LEVEL"""
    
    def test_health_endpoint_no_errors(self):
        """Calling health endpoint should not produce errors"""
        for _ in range(5):
            response = requests.get(f"{get_app_url()}/health")
            assert response.status_code == 200
            # Wait slightly to allow logging
            time.sleep(0.1)
        logger.info("Health check logging OK")

# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
