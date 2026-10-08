from django.contrib.auth.models import Group, User
from django.test import TestCase


class LoginTests(TestCase):
    def setUp(self):
        User.objects.create_user("marketer", password="demo123").groups.add(Group.objects.get(name="Marketer"))
        User.objects.create_user("admin", password="admin123").groups.add(Group.objects.get(name="Admin"))

    def login(self, username, password):
        return self.client.post("/api/v1/auth/login", {"username": username, "password": password},
                                content_type="application/json")

    def test_login_returns_tokens_and_role(self):
        for username, password, role in [("marketer", "demo123", "marketer"), ("admin", "admin123", "admin")]:
            res = self.login(username, password)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["user"], {"username": username, "role": role})
            self.assertIn("access", res.json())
            self.assertIn("refresh", res.json())

    def test_wrong_password_401(self):
        self.assertEqual(self.login("marketer", "sai").status_code, 401)
