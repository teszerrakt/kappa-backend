#!/usr/bin/env bash

# Production-ready gunicorn configuration
gunicorn wsgi:app \
  --bind 0.0.0.0:${PORT:-80} \
  --workers ${WORKERS:-4} \
  --worker-class sync \
  --timeout 120 \
  --log-level ${LOG_LEVEL:-info} \
  --access-logfile - \
  --error-logfile - \
  --preload