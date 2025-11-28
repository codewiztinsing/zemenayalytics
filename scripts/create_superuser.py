#!/usr/bin/env python
"""
Django script to create a superuser if it doesn't exist.
Reads credentials from environment variables.
"""
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Get credentials from environment variables with defaults
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

# Check if superuser already exists
if User.objects.filter(username=username).exists():
    print(f"Superuser '{username}' already exists. Skipping creation.")
    sys.exit(0)

# Create superuser
try:
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully!")
except Exception as e:
    print(f"Error creating superuser: {e}")
    sys.exit(1)

