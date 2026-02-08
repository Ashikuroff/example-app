"""Integration tests for the Flask server.

These tests start the Flask app in a background server thread using
Werkzeug's make_server so tests can reliably hit http://localhost:5000
without depending on external background processes started by CI steps.
"""

import time
import pytest
import requests
from threading import Thread
from werkzeug.serving import make_server

# Import the Flask app
from src.server import app


BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 5


class ServerThread(Thread):
    def __init__(self, app, host="127.0.0.1", port=5000):
        Thread.__init__(self)
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.daemon = True

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="session", autouse=True)
def start_flask_server():
    """Start the Flask app in a background thread for the duration of the test session."""
    server = ServerThread(app)
    server.start()

    # Wait until the health endpoint responds
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    yield

    server.shutdown()


class TestHealthy:
    """Integration tests for application health."""
    
    def test_app_is_accessible(self):
        """Test that the application is accessible."""
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
    
    def test_health_endpoint_returns_healthy(self):
        """Test that health endpoint returns healthy status."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_metrics_endpoint_accessible(self):
        """Test that metrics endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
        assert response.status_code == 200
        assert b"prometheus" in response.content.lower() or b"app_requests_total" in response.content


class TestAPI:
    """Integration tests for API endpoints."""
    
    def test_hello_returns_json(self):
        """Test that hello endpoint returns proper JSON."""
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert "version" in data
    
    def test_404_handling(self):
        """Test that undefined endpoints return 404."""
        response = requests.get(f"{BASE_URL}/undefined-endpoint", timeout=TIMEOUT)
        assert response.status_code == 404
        
        data = response.json()
        assert data.get("error") == "Not found"
    
    def test_concurrent_requests(self):
        """Test that app handles concurrent requests."""
        import concurrent.futures
        
        def make_request():
            response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(results), "Not all concurrent requests succeeded"


class TestMetrics:
    """Integration tests for Prometheus metrics."""
    
    def test_metrics_contain_request_count(self):
        """Test that metrics include request count."""
        # Make a request to generate metrics
        requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        
        # Fetch metrics
        response = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Verify it contains request metrics
        content = response.text
        assert "app_requests_total" in content
        assert "app_request_duration_seconds" in content
    
    def test_metrics_format_is_prometheus(self):
        """Test that metrics are in Prometheus format."""
        response = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Prometheus format should have TYPE and HELP lines
        content = response.text
        assert "# HELP" in content or "app_requests_total" in content
        
        # Should have content-type header for Prometheus
        assert "text/plain" in response.headers.get("Content-Type", "")


class TestPerformance:
    """Integration tests for performance characteristics."""
    
    def test_response_time_acceptable(self):
        """Test that response times are acceptable (< 100ms)."""
        start = time.time()
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        duration = (time.time() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert duration < 100, f"Response took {duration:.0f}ms (expected < 100ms)"
    
    def test_no_memory_leaks(self):
        """Test that making many requests doesn't cause obvious issues."""
        import gc
        
        # Make many requests
        for _ in range(50):
            response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
            assert response.status_code == 200
        
        # Force garbage collection
        gc.collect()
        
        # Final health check should still work
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
