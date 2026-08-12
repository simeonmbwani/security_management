from django.contrib.auth import authenticate, get_user_model

User = get_user_model()
u = User.objects.get(username='simeonmbwani')
print('has_password', bool(u.password))
print('password_hash', u.password[:80])
for candidate in ['@A1n2d3y4', '@A1n2d3y4.', '@A1n2d3y4!']:
    print(candidate, '=>', authenticate(username='simeonmbwani', password=candidate) is not None)
