#!/usr/bin/env bash

DB_PATH=${KAPPA_DB_PATH:-kappa.db}
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}./src"

if [ ! -s "$DB_PATH" ]; then
  python src/scripts/migrate.py
fi

gunicorn wsgi:app --preload --config gunicorn.conf.py --bind 0.0.0.0:80 --log-level=debug --workers=2
