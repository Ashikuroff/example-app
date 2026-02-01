#!/bin/bash
# Local Development Server
# Starts the Flask server with hot-reload and logging
# Usage: ./scripts/server.sh [--port <port>] [--debug]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=5000
DEBUG=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="$2"
      shift 2
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--port <port>] [--debug]"
      echo "  --port        Port to listen on (default: 5000)"
      echo "  --debug       Enable debug mode (auto-reload)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

cd "$SCRIPT_DIR"

# Check for Python venv
if [ ! -d ".venv" ]; then
  echo "ERROR: Virtual environment not found at .venv" >&2
  exit 1
fi

PYTHON=".venv/bin/python"

# Export env vars
export FLASK_PORT="$PORT"
export FLASK_DEBUG=$([ "$DEBUG" = true ] && echo "true" || echo "false")
export FLASK_APP="src.server:app"

echo "Starting Flask server..."
echo "  Port: $PORT"
echo "  Debug: $DEBUG"
echo "  Endpoints:"
echo "    GET  http://localhost:$PORT/       (hello)"
echo "    GET  http://localhost:$PORT/health (health check)"
echo "    GET  http://localhost:$PORT/metrics (Prometheus metrics)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

$PYTHON -m src.server
