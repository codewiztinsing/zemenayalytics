#!/bin/bash
set -e

echo "Populating database with test data..."
python manage.py populate_data

echo "Data population completed!"

