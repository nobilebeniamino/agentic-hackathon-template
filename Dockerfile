# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set up working directory
WORKDIR /app

# Install system dependencies including audio processing tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create media directory and set permissions
RUN mkdir -p /app/media && \
    chmod 755 /app/media && \
    chown -R nobody:nogroup /app/media

# Create a volume for media files persistence
VOLUME ["/app/media"]

# Test media directory at build time
RUN touch /app/media/test_build.txt && \
    ls -la /app/media/ && \
    rm /app/media/test_build.txt

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Move into Django project directory where manage.py lives
WORKDIR /app/ai_first_response

# Create media directory for runtime file uploads
RUN mkdir -p /app/ai_first_response/media/audio /app/ai_first_response/media/voice

# Collect static files
RUN python manage.py collectstatic --noinput

# Set proper permissions for media directory
RUN chmod -R 755 /app/ai_first_response/media

# Expose port
EXPOSE $PORT

# Use custom entrypoint script
CMD ["/app/entrypoint.sh"]