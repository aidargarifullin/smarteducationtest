from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User


class RegistrationTestCase(APITestCase):
    """

    """
    def test_registration(self):
        url = reverse('register')
        data = {
            "username": "newuser",
            "password": "strongpassword123",
            "password2": "strongpassword123",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)
