from django.test import TestCase, Client
from lms.models import User
import json

class AuthAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@test.com", password="password123", role="student")
        self.register_url = "/api/auth/register"
        self.login_url = "/api/auth/login"

    def test_register_success(self):
        """Test register berhasil -> return token"""
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "newpassword123",
            "role": "student"
        }
        response = self.client.post(self.register_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.json())

    def test_login_success(self):
        """Test login sukses -> JWT valid"""
        data = {
            "username": "testuser",
            "password": "password123"
        }
        response = self.client.post(self.login_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())

    def test_login_failed(self):
        """Test login gagal (password salah) -> 401"""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_without_token(self):
        """Test akses endpoint protected tanpa token -> 401"""
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
