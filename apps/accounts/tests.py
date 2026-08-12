from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class UserEmployeeNumberTests(TestCase):
    def test_blank_employee_number_is_generated(self):
        User = get_user_model()

        user = User.objects.create(username='autogen-user', employee_number='')

        self.assertTrue(user.employee_number)
        self.assertNotEqual(user.employee_number, '')


class UserRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_public_registration_creates_guard_and_employee_number(self):
        response = self.client.post(
            reverse('user-register'),
            {
                'username': 'newguard',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
                'first_name': 'Asha',
                'last_name': 'Njeri',
                'email': 'asha@example.com',
                'phone': '0712345678',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='newguard')
        self.assertEqual(user.role, 'guard')
        self.assertTrue(user.employee_number)
        self.assertTrue(user.guard_profile)

    def test_login_accepts_employee_number(self):
        user = get_user_model().objects.create_user(
            username='empguard',
            password='StrongPass123!',
            employee_number='EMP-1001',
        )

        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': user.employee_number, 'password': 'StrongPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
