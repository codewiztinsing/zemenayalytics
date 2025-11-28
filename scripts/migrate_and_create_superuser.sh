#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser..."
python scripts/create_superuser.py

echo "Migration and superuser setup completed!"

