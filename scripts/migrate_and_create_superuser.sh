#!/bin/bash
set -e

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static files collection skipped or failed"

echo "Creating superuser..."
python scripts/create_superuser.py

echo "Migration and superuser setup completed!"

