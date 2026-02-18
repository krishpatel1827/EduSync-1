#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate

# Load production data from fixtures first (runs only if database is empty)
python manage.py load_production_data

# Create superuser from environment variables (if DJANGO_SUPERUSER_PASSWORD is set and no admin exists)
python manage.py create_superuser_if_none
