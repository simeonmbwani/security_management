#!/usr/init/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

# Run accounts migration explicitly first so accounts_user exists
python manage.py migrate accounts --no-input

# Run the rest of the migrations
python manage.py migrate --no-input

# Collect static files last
python manage.py collectstatic --no-input