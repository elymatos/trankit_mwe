"""
Gunicorn configuration for Trankit MWE API
"""

import json
import multiprocessing
import os

# Worker configuration
workers_per_core_str = os.getenv("WORKERS_PER_CORE", "1")
max_workers_str = os.getenv("MAX_WORKERS", "1")  # Default to 1 for GPU
use_max_workers = int(max_workers_str) if max_workers_str else None
web_concurrency_str = os.getenv("WEB_CONCURRENCY", None)

# Host and port
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "80")
bind_env = os.getenv("BIND", None)

if bind_env:
    use_bind = bind_env
else:
    use_bind = f"{host}:{port}"

# Worker calculation
cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores

if web_concurrency_str:
    web_concurrency = int(web_concurrency_str)
    assert web_concurrency > 0, "WEB_CONCURRENCY must be positive"
else:
    web_concurrency = max(int(default_web_concurrency), 2)
    if use_max_workers:
        web_concurrency = min(web_concurrency, use_max_workers)

# For GPU: force to 1 worker
gpu_enabled = os.getenv("GPU_ENABLED", "false").lower() in ("true", "1", "yes")
if gpu_enabled:
    web_concurrency = 1
    print("GPU mode enabled: Using 1 worker")

# Logging
use_loglevel = os.getenv("LOG_LEVEL", "info")
accesslog_var = os.getenv("ACCESS_LOG", "-")
use_accesslog = accesslog_var or None
errorlog_var = os.getenv("ERROR_LOG", "-")
use_errorlog = errorlog_var or None

# Timeouts (important for NLP processing)
graceful_timeout_str = os.getenv("GRACEFUL_TIMEOUT", "600")
timeout_str = os.getenv("TIMEOUT", "600")  # 10 minutes for large texts
keepalive_str = os.getenv("KEEP_ALIVE", "5")

# Gunicorn config variables
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
errorlog = use_errorlog
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance
accesslog = use_accesslog
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)

# Worker class
worker_class = "uvicorn.workers.UvicornWorker"

# Preload app for better memory usage
preload_app = True

# For debugging and testing
log_data = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    "graceful_timeout": graceful_timeout,
    "timeout": timeout,
    "keepalive": keepalive,
    "errorlog": errorlog,
    "accesslog": accesslog,
    "worker_class": worker_class,
    "preload_app": preload_app,
    # Additional, non-gunicorn variables
    "workers_per_core": workers_per_core,
    "use_max_workers": use_max_workers,
    "host": host,
    "port": port,
    "gpu_enabled": gpu_enabled,
}

print("Gunicorn Configuration:")
print(json.dumps(log_data, indent=2))
