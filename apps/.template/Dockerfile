FROM python:3.11-slim as base

RUN mkdir /work/
WORKDIR /work/

# Create non-root user and group first
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy requirements and install dependencies
COPY ./src/requirements.txt /work/requirements.txt
RUN pip install --no-cache-dir -r /work/requirements.txt

# Copy application code
COPY --chown=appuser:appgroup ./src/ /work/

ENV FLASK_APP=server.py

# Switch to non-root user
USER appuser

###########START NEW IMAGE: DEBUGGER ###################
FROM base as debug
RUN pip install ptvsd

CMD python -m ptvsd --host 0.0.0.0 --port 5678 --wait --multiprocess -m flask run -h 0.0.0.0 -p 5000

###########START NEW IMAGE: PRODUCTION ###################
FROM base as prod

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
