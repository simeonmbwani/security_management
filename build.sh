#!/usr/bin/env bash
# Exit on error
set -o errexit

# Step 1: Install Python dependencies first
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Step 2: Run database migrations
python manage.py migrate

# Step 3: Create or update your superuser
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user, created = User.objects.get_or_create(
    username='simeonmbwani', 
    defaults={
        'email': 'simeonmbwani@gmail.com', 
        'is_staff': True, 
        'is_superuser': True
    }
)
admin_user.set_password('@A1n2d3y4')
admin_user.save()
print('Superuser password ensured.')
"

# Step 4: Collect static files
python manage.py collectstatic --no-input