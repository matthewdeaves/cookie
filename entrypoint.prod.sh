#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=cookie.settings

# Data directory for persistent storage
DATA_DIR="/app/data"
mkdir -p "$DATA_DIR/media" 2>/dev/null || {
    echo "Warning: Could not create $DATA_DIR/media - ensure volume has correct permissions"
}

# Generate secret key if not provided
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY_FILE="$DATA_DIR/.secret_key"
    if [ ! -f "$SECRET_KEY_FILE" ]; then
        echo "Generating new secret key..."
        python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > "$SECRET_KEY_FILE"
        chmod 600 "$SECRET_KEY_FILE"
    fi
    export SECRET_KEY=$(cat "$SECRET_KEY_FILE")
fi

# Wait for PostgreSQL if configured
if [[ "$DATABASE_URL" == postgres* ]] || [[ "$DATABASE_URL" == postgresql* ]]; then
    echo "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if python -c "
import django
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; then
            echo "PostgreSQL is ready!"
            break
        fi
        echo "Waiting for database... ($i/30)"
        sleep 2
        if [ "$i" -eq 30 ]; then
            echo "Database not available after 60s, exiting."
            exit 1
        fi
    done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Ensure app user owns required directories
chown -R app:app /app/staticfiles /app/data 2>/dev/null || true

# Set up and start cron for device code cleanup (hourly)
# Cron daemonizes itself — start it before supervised processes
echo "DJANGO_SETTINGS_MODULE=cookie.settings" > /etc/cron.d/cookie-cleanup
echo "DATABASE_URL=${DATABASE_URL}" >> /etc/cron.d/cookie-cleanup
echo "SECRET_KEY=${SECRET_KEY}" >> /etc/cron.d/cookie-cleanup
echo "0 * * * * root cd /app && /usr/local/bin/python manage.py cleanup_device_codes >> /proc/1/fd/1 2>&1" >> /etc/cron.d/cookie-cleanup
echo "15 3 * * * root cd /app && /usr/local/bin/python manage.py cleanup_sessions >> /proc/1/fd/1 2>&1" >> /etc/cron.d/cookie-cleanup
echo "30 3 * * * root cd /app && /usr/local/bin/python manage.py cleanup_search_images >> /proc/1/fd/1 2>&1" >> /etc/cron.d/cookie-cleanup
chmod 0600 /etc/cron.d/cookie-cleanup
crontab /etc/cron.d/cookie-cleanup
cron
echo "Cron daemon started: device codes (hourly), sessions + images (daily 3am)"

# Process supervision: if either process exits, terminate the other and exit
cleanup() {
    echo "Shutting down..."
    kill -TERM "$GUNICORN_PID" "$NGINX_PID" 2>/dev/null
    wait "$GUNICORN_PID" "$NGINX_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start Gunicorn as the non-root app user (binds to localhost only, nginx proxies to it)
echo "Starting Gunicorn on 127.0.0.1:8000..."
su -s /bin/bash app -c "gunicorn \
    --bind 127.0.0.1:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile /dev/null \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    cookie.wsgi:application" &
GUNICORN_PID=$!

# Start Nginx in background (requires root for port 80)
echo "Starting Nginx on 0.0.0.0:80..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Wait for either process to exit, then terminate the other
wait -n
echo "Process exited unexpectedly, shutting down..."
cleanup
