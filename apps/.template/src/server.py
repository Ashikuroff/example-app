import os
import logging
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
import time

app = Flask(__name__)

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)
request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint'],
    registry=REGISTRY
)

# Middleware to track request duration
@app.before_request
def before_request():
    app.request_start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - app.request_start_time
    request_duration.labels(endpoint=request.endpoint or 'unknown').observe(duration)
    request_count.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=str(response.status_code)
    ).inc()
    return response

@app.route("/")
def hello():
    logger.info("Hello endpoint called")
    return jsonify({
        "message": "Hello from {APP_NAME}!",
        "version": "1.0.0",
        "service": "{APP_NAME}"
    }), 200

@app.route("/health")
def health():
    """Health check endpoint for Kubernetes probes"""
    logger.debug("Health check endpoint called")
    return jsonify({"status": "healthy"}), 200

@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

@app.route("/about")
def about():
    logger.info("About endpoint called")
    return jsonify({
        "app": "{APP_NAME}",
        "version": "1.0.0",
        "environment": os.getenv('FLASK_ENV', 'development')
    }), 200

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"Not found: {request.path}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=log_level == 'DEBUG')
