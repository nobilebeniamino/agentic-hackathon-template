# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set up working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Move into Django project directory where manage.py lives
WORKDIR /app/ai_first_response

# Collect static files if any (ignore errors)
RUN python manage.py collectstatic --noinput || true

# Expose port and run Gunicorn
CMD ["gunicorn", "ai_first_response.wsgi:application", "--bind", "0.0.0.0:8080"]