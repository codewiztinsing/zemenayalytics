"""
Pytest configuration for Django tests.
"""
import os

# Set default environment variable for settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('PIPELINE', 'local')

