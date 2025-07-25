# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# ===== System dependencies =====
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ===== Python dependencies =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== Project source =====
COPY . .

# ===== Optional: collect static files (safe if none exist) =====
RUN python manage.py collectstatic --noinput || true

# ===== Launch gunicorn on Cloud Run’s default port =====
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8080"]
