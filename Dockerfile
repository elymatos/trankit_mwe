FROM tiangolo/uvicorn-gunicorn:python3.9

LABEL maintainer="Trankit MWE API"

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements-api.txt /tmp/requirements-api.txt
RUN pip install --no-cache-dir -r /tmp/requirements-api.txt

# Copy application code
COPY ./app /app/app

# Copy trankit source code (needed for MWE extension)
COPY ./trankit /app/trankit

# Copy prestart script
COPY ./app/prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

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

# Expose port
EXPOSE 80
