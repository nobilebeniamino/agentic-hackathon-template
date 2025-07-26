#!/bin/bash
set -e

# Test and ensure media directory is accessible
echo "Testing media directory..."
MEDIA_DIR="/app/media"

if [ ! -d "$MEDIA_DIR" ]; then
    echo "Creating media directory..."
    mkdir -p "$MEDIA_DIR"
fi

chmod 755 "$MEDIA_DIR"
echo "Media directory permissions: $(ls -ld $MEDIA_DIR)"

# Test write access
if touch "$MEDIA_DIR/test_startup.txt" 2>/dev/null; then
    echo "✅ Media directory is writable"
    rm "$MEDIA_DIR/test_startup.txt"
else
    echo "❌ Media directory is NOT writable"
    exit 1
fi

echo "Starting AI First Response application..."

# Function to check if database is ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    for i in {1..30}; do
        if python manage.py check --database default >/dev/null 2>&1; then
            echo "Database is ready!"
            break
        else
            echo "Waiting for database... attempt $i/30"
            sleep 2
        fi
    done
}

# Wait for database
wait_for_db

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput || {
    echo "Migration failed, but continuing..."
    sleep 5
}

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || {
    echo "Static files collection failed, but continuing..."
}

# Create superuser if needed (optional)
echo "Creating default superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
" || echo "Superuser creation skipped"

# Start Gunicorn
echo "Starting Gunicorn server on port $PORT..."
exec gunicorn ai_first_response.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info
