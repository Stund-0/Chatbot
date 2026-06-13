#!/bin/sh
set -e

PORT="${PORT:-5000}"

exec gunicorn wsgi:app --bind "0.0.0.0:${PORT}" --workers 2 --timeout 120 --access-logfile - --error-logfile -
