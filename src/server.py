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

# Prometheus metrics (explicitly using default registry to prevent duplication)
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
        "message": "Hello World!",
        "version": "1.0.0",
        "service": "example-app"
    }), 200

@app.route("/health")
def health():
    logger.info("Health check performed")
    return jsonify({
        "status": "healthy",
        "service": "example-app"
    }), 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), mimetype='text/plain; charset=utf-8')

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"Route not found: {request.path}")
    return jsonify({
        "error": "Not found",
        "path": request.path
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error"
    }), 500

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    logger.info(f"Starting Flask app on port {port}, debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)

