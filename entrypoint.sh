#!/bin/bash
set -e

echo "Waiting for database..."
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-30}"
elapsed=0
until DJANGO_SETTINGS_MODULE=cookie.settings python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
  elapsed=$((elapsed + 2))
  if [ "$elapsed" -ge "$DB_WAIT_TIMEOUT" ]; then
    echo "Database not available after ${DB_WAIT_TIMEOUT}s"
    exit 1
  fi
  echo "Waiting for database..."
  sleep 2
done
echo "Database is available."

# Install dev tools if in development mode
if [ "$DEV_TOOLS" = "1" ] && [ -f requirements-dev.txt ]; then
  echo "Installing dev tools..."
  pip install --quiet --no-cache-dir -r requirements-dev.txt
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --reload --workers 2 --threads 2 cookie.wsgi:application
