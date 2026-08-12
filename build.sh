python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user, created = User.objects.get_or_create(username='simeonmbwani', defaults={'email': 'simeonmbwani@gmail.com', 'is_staff': True, 'is_superuser': True})
admin_user.set_password('@A1n2d3y4')
admin_user.save()
print('Superuser password ensured.')
"