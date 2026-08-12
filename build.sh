#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Automatically create a default superuser if none exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('simeonmbwani', 'simeonmbwani@gmail.com', '@A1n2d3y4')
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
"

# Collect static files (if applicable)
python manage.py collectstatic --no-input