from django.contrib.auth.models import User
from django.test import TestCase


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("marketer", password="demo123")

    def login(self, username, password):
        return self.client.post("/api/v1/auth/login", {"username": username, "password": password},
                                content_type="application/json")

    def test_login_returns_tokens_and_user(self):
        res = self.login("marketer", "demo123")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"], {"username": "marketer"})
        self.assertIn("access", res.json())
        self.assertIn("refresh", res.json())

    def test_wrong_password_401(self):
        self.assertEqual(self.login("marketer", "sai").status_code, 401)

    def test_refresh_returns_new_access(self):
        refresh = self.login("marketer", "demo123").json()["refresh"]
        res = self.client.post("/api/v1/auth/refresh", {"refresh": refresh}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())
        bad = self.client.post("/api/v1/auth/refresh", {"refresh": "sai"}, content_type="application/json")
        self.assertEqual(bad.status_code, 401)
