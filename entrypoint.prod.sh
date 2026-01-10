#!/bin/bash
set -e

# Data directory for persistent storage
DATA_DIR="/app/data"
mkdir -p "$DATA_DIR/media" 2>/dev/null || {
    echo "Warning: Could not create $DATA_DIR/media - ensure volume has correct permissions"
}

# Link database to data directory if not already there
if [ ! -f "$DATA_DIR/db.sqlite3" ]; then
    echo "Initializing database..."
fi

# Use data directory for database
export DATABASE_PATH="$DATA_DIR/db.sqlite3"

# Generate secret key if not provided
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY_FILE="$DATA_DIR/.secret_key"
    if [ ! -f "$SECRET_KEY_FILE" ]; then
        echo "Generating new secret key..."
        python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > "$SECRET_KEY_FILE"
    fi
    export SECRET_KEY=$(cat "$SECRET_KEY_FILE")
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn on 0.0.0.0:8000..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-4} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance \
    cookie.wsgi:application
