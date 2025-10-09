FROM tiangolo/uvicorn-gunicorn:python3.9

LABEL maintainer="Trankit MWE API"

# Set working directory
WORKDIR /app

# Install Trankit core dependencies first (cached layer)
# Use --retries and --timeout to handle network issues
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r /tmp/requirements.txt || \
    (echo "Warning: Some packages failed to install. Retrying..." && \
     pip install --no-cache-dir --retries 3 --timeout 60 -r /tmp/requirements.txt)

# Install API-specific dependencies (minimal, fast)
COPY requirements-docker.txt /tmp/requirements-docker.txt
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r /tmp/requirements-docker.txt

# Copy trankit source code (needed for MWE extension)
COPY ./trankit /app/trankit

# Copy application code
COPY ./app /app/app

# Copy prestart script
COPY ./app/prestart.sh /app/prestart.sh
# Convert line endings and make executable (in case of CRLF issues)
RUN sed -i 's/\r$//' /app/prestart.sh && chmod +x /app/prestart.sh

# Create directories for data and cache
RUN mkdir -p /app/data/portuguese /app/cache/trankit

# Environment variables (can be overridden in docker-compose or at runtime)
ENV MODULE_NAME="app.main"
ENV VARIABLE_NAME="app"
ENV PORT=80
ENV WORKERS_PER_CORE=1
ENV MAX_WORKERS=1
ENV GPU_ENABLED=false
ENV DEFAULT_LANGUAGE=portuguese
ENV MWE_ENABLED=true
ENV LOG_LEVEL=info
ENV PYTHONPATH=/app

# Expose port
EXPOSE 80
