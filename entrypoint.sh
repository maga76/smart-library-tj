#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Seeding database..."
python manage.py seed_data

echo "Starting server..."
gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
