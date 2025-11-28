#!/bin/bash
set -e

echo "Running Django tests..."
python manage.py test apps.analytics.tests.test_models apps.analytics.tests.test_services apps.analytics.tests.test_views --verbosity=2

echo "All tests completed!"

