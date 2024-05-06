# Base image (compatible with Python 3.11)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (optional, for psutil)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev libffi-dev && apt-get clean

# Install dependencies
RUN pip install streamlit psutil datetime

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Entrypoint command (replace with your main script name)
CMD ["streamlit","run", "app.py"]  # Replace "main.py" with your actual main script name

