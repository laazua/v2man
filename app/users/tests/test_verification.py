"""Tests for email verification registration flow."""

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from users.models import User


class BrokenEmailBackend(BaseEmailBackend):
    """Email backend that always raises an exception."""

    def send_messages(self, messages):
        raise ConnectionError("模拟邮件服务器不可用")


class VerificationRegistrationTest(TestCase):
    """Test email verification during registration."""

    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        }

    def test_register_creates_inactive_user_and_sends_code(self):
        """注册后用户为未激活状态，且收到验证码邮件"""
        resp = self.client.post("/api/auth/register/", self.register_data)
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(username="testuser")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("邮箱验证", mail.outbox[0].subject)

    def test_activate_with_valid_code(self):
        """有效验证码可激活用户"""
        self.client.post("/api/auth/register/", self.register_data)
        user = User.objects.get(username="testuser")
        # 从邮件提取验证码
        body = mail.outbox[0].body
        code = body.split("验证码是：")[1].split("\n")[0].strip()

        resp = self.client.post(
            "/api/auth/activate/",
            {
                "email": "test@example.com",
                "code": code,
            },
        )
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_wrong_code(self):
        """错误验证码返回 400"""
        self.client.post("/api/auth/register/", self.register_data)
        resp = self.client.post(
            "/api/auth/activate/",
            {
                "email": "test@example.com",
                "code": "000000",
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_activate_expired_code(self):
        """过期验证码返回 400"""
        self.client.post("/api/auth/register/", self.register_data)
        user = User.objects.get(username="testuser")
        # 模拟过期
        from django.core.cache import cache

        cache.delete(f"verify_code_{user.email}")
        resp = self.client.post(
            "/api/auth/activate/",
            {
                "email": "test@example.com",
                "code": "123456",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("已过期", resp.json()["error"])

    def test_inactive_user_cannot_login(self):
        """未激活用户无法登录"""
        self.client.post("/api/auth/register/", self.register_data)
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_resend_code(self):
        """重发验证码接口发送新验证码"""
        self.client.post("/api/auth/register/", self.register_data)
        # 清空邮件列表，模拟第一次邮件已发送
        mail.outbox = []
        resp = self.client.post(
            "/api/auth/verification-code/resend/",
            {
                "email": "test@example.com",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("邮箱验证", mail.outbox[0].subject)

    def test_activate_with_duplicate_email(self):
        """同一邮箱多次注册，激活时取第一个未激活用户"""
        User.objects.create_user(
            "dup1", "dup@test.com", "testpass123", is_active=False
        )
        User.objects.create_user(
            "dup2", "dup@test.com", "testpass123", is_active=False
        )
        from django.core.cache import cache

        cache.set("verify_code_dup@test.com", "123456", 300)
        resp = self.client.post(
            "/api/auth/activate/",
            {
                "email": "dup@test.com",
                "code": "123456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.get(username="dup1").is_active)

    @override_settings(
        EMAIL_BACKEND="users.tests.test_verification.BrokenEmailBackend"
    )
    def test_register_rolls_back_user_on_email_failure(self):
        """邮件发送失败时，用户不入库"""
        resp = self.client.post(
            "/api/auth/register/",
            {
                "username": "rollbacktest",
                "email": "rollback@test.com",
                "password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 500)
        self.assertFalse(User.objects.filter(username="rollbacktest").exists())
