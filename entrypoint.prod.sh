#!/bin/bash
set -e

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
    done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating cache table..."
python manage.py createcachetable

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Process supervision: if either process exits, terminate the other and exit
cleanup() {
    echo "Shutting down..."
    kill -TERM "$GUNICORN_PID" "$NGINX_PID" 2>/dev/null
    wait "$GUNICORN_PID" "$NGINX_PID" 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start Gunicorn in background (binds to localhost only, nginx proxies to it)
echo "Starting Gunicorn on 127.0.0.1:8000..."
gunicorn \
    --bind 127.0.0.1:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    cookie.wsgi:application &
GUNICORN_PID=$!

# Start Nginx in background
echo "Starting Nginx on 0.0.0.0:80..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Wait for either process to exit, then terminate the other
wait -n
echo "Process exited unexpectedly, shutting down..."
cleanup
