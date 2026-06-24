"""Tests for authentication, profile, recharge, password reset, and payments."""

import hashlib

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from invite.models import SystemSetting
from nodes.subscription import Subscription
from plans.models import Plan
from users.backends import UsernameOrEmailBackend
from users.models import User
from users.wallet import PaymentOrder, Recharge, Wallet

token_generator = PasswordResetTokenGenerator()


class UsernameOrEmailBackendTest(TestCase):
    """Test the custom authentication backend."""

    def setUp(self):
        self.backend = UsernameOrEmailBackend()
        self.user = User.objects.create_user(
            "testuser",
            "test@example.com",
            "testpass123",
        )

    def test_authenticate_with_username(self):
        """用 username 登录成功返回用户"""
        result = self.backend.authenticate(
            None,
            username="testuser",
            password="testpass123",
        )
        self.assertEqual(result, self.user)

    def test_authenticate_with_email(self):
        """用 email 登录成功返回用户"""
        result = self.backend.authenticate(
            None,
            username="test@example.com",
            password="testpass123",
        )
        self.assertEqual(result, self.user)

    def test_authenticate_nonexistent_user_returns_none(self):
        """用户不存在返回 None"""
        result = self.backend.authenticate(
            None,
            username="nobody",
            password="testpass123",
        )
        self.assertIsNone(result)

    def test_authenticate_wrong_password_returns_none(self):
        """密码错误返回 None"""
        result = self.backend.authenticate(
            None,
            username="testuser",
            password="wrongpass",
        )
        self.assertIsNone(result)

    def test_authenticate_empty_username_returns_none(self):
        """空用户名返回 None"""
        result = self.backend.authenticate(
            None,
            username="",
            password="testpass123",
        )
        self.assertIsNone(result)

    def test_authenticate_empty_password_returns_none(self):
        """空密码返回 None"""
        result = self.backend.authenticate(
            None,
            username="testuser",
            password="",
        )
        self.assertIsNone(result)


class LoginTest(TestCase):
    """Test JWT login and token refresh."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "testuser",
            "test@example.com",
            "testpass123",
        )

    def test_login_success_returns_access_and_refresh(self):
        """登录成功返回 access 和 refresh token"""
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())
        self.assertIn("refresh", resp.json())

    def test_login_with_email_success(self):
        """使用 email 登录成功"""
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "test@example.com",
                "password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 200)

    def test_login_wrong_password_returns_401(self):
        """用户名/密码错误返回 401"""
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "wrongpass",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_login_nonexistent_user_returns_401(self):
        """不存在的用户返回 401"""
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "nobody",
                "password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_refresh_token_returns_new_access(self):
        """有效 refresh token 返回新 access token"""
        login_resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        refresh = login_resp.json()["refresh"]
        resp = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": refresh,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_refresh_invalid_token_returns_401(self):
        """无效 refresh token 返回 401"""
        resp = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": "invalid_token_here",
            },
        )
        self.assertEqual(resp.status_code, 401)


class ProfileViewTest(TestCase):
    """Test profile retrieval and update."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "testuser",
            "test@example.com",
            "testpass123",
        )
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.balance = 5000
        wallet.save()
        Subscription.objects.get_or_create(user=self.user)

    def _auth(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_profile_returns_user_info(self):
        """GET 返回用户信息包含余额、uuid、订阅token等"""
        self._auth()
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["balance"], 5000)
        self.assertIsNotNone(data["uuid"])
        self.assertIsNotNone(data["subscription_token"])
        self.assertIn("date_joined", data)

    def test_profile_unauthenticated_returns_401(self):
        """未认证访问返回 401"""
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, 401)

    def test_profile_patch_email_and_password(self):
        """PATCH 修改 email 和密码"""
        self._auth()
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "email": "new@example.com",
                "old_password": "testpass123",
                "new_password": "newpass456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertTrue(self.user.check_password("newpass456"))

    def test_profile_patch_wrong_old_password_returns_400(self):
        """PATCH 旧密码错误返回 400"""
        self._auth()
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "old_password": "wrongpass",
                "new_password": "newpass456",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("原密码不正确", resp.json()["error"])

    def test_profile_patch_email_only(self):
        """PATCH 修改 email 需验证密码"""
        self._auth()
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "email": "onlyemail@example.com",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("修改邮箱需要验证密码", resp.json()["error"])

    def test_profile_patch_email_with_password(self):
        """PATCH 修改 email 同时提供密码"""
        self._auth()
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "email": "validated@example.com",
                "old_password": "testpass123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "validated@example.com")

    def test_profile_patch_password_only(self):
        """PATCH 只修改密码"""
        self._auth()
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "old_password": "testpass123",
                "new_password": "newpass456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))

    def test_profile_unauthorized_patch_returns_401(self):
        """未认证 PATCH 返回 401"""
        resp = self.client.patch(
            "/api/auth/profile/",
            {
                "email": "test@example.com",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_profile_plan_name(self):
        """有套餐时返回套餐名称"""
        plan = Plan.objects.create(
            name="白银套餐",
            price=5.00,
            traffic_limit=1024,
            duration_days=30,
        )
        self.user.plan = plan
        self.user.save()
        self._auth()
        resp = self.client.get("/api/auth/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["plan_name"], "白银套餐")


class RechargeViewTest(TestCase):
    """Test recharge history and submission."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "testuser",
            "test@example.com",
            "testpass123",
        )

    def _auth(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_recharge_get_returns_history(self):
        """GET 返回充值历史列表"""
        Recharge.objects.create(
            user=self.user, amount=1000, status="completed"
        )
        Recharge.objects.create(user=self.user, amount=2000, status="pending")
        self._auth()
        resp = self.client.get("/api/auth/recharge/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["amount"], 2000)
        self.assertEqual(data[1]["amount"], 1000)

    def test_recharge_post_creates_recharge(self):
        """POST 提交充值申请"""
        self._auth()
        resp = self.client.post("/api/auth/recharge/", {"amount": 3000})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.assertEqual(Recharge.objects.count(), 1)
        self.assertEqual(Recharge.objects.first().amount, 3000)

    def test_recharge_post_duplicate_pending_returns_400(self):
        """已有待确认充值申请时返回 400"""
        Recharge.objects.create(user=self.user, amount=1000, status="pending")
        self._auth()
        resp = self.client.post("/api/auth/recharge/", {"amount": 3000})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("请扫码付款", resp.json()["error"])

    def test_recharge_post_invalid_amount_returns_400(self):
        """无效金额返回 400"""
        self._auth()
        resp = self.client.post("/api/auth/recharge/", {"amount": "abc"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("无效金额", resp.json()["error"])

    def test_recharge_post_amount_zero_returns_400(self):
        """金额为0返回 400"""
        self._auth()
        resp = self.client.post("/api/auth/recharge/", {"amount": 0})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("金额必须大于0", resp.json()["error"])

    def test_recharge_unauthenticated_get_returns_401(self):
        """未认证 GET 返回 401"""
        resp = self.client.get("/api/auth/recharge/")
        self.assertEqual(resp.status_code, 401)

    def test_recharge_unauthenticated_post_returns_401(self):
        """未认证 POST 返回 401"""
        resp = self.client.post("/api/auth/recharge/", {"amount": 1000})
        self.assertEqual(resp.status_code, 401)


class PasswordResetTest(TestCase):
    """Test password reset request and confirmation."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "resetuser",
            "reset@example.com",
            "oldpass123",
        )

    def test_password_reset_request_sends_email(self):
        """POST 发送重置邮件"""
        resp = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "reset@example.com",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("密码重置", mail.outbox[0].subject)
        self.assertIn("reset@example.com", mail.outbox[0].to)

    def test_password_reset_request_nonexistent_email_returns_success(self):
        """邮箱不存在返回 200（防止信息泄漏）"""
        resp = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "nobody@example.com",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("如果该邮箱已注册", resp.json()["message"])

    def test_password_reset_confirm_with_valid_token(self):
        """使用有效 token 重置密码"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)
        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "password": "newsecure456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecure456"))

    def test_password_reset_confirm_invalid_token_returns_400(self):
        """无效 token 返回 400"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": "invalid-token",
                "password": "newsecure456",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("已过期或无效", resp.json()["error"])

    def test_password_reset_confirm_invalid_uid_returns_400(self):
        """无效 uid 返回 400"""
        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": "invalid-uid",
                "token": "some-token",
                "password": "newsecure456",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("无效的链接", resp.json()["error"])

    def test_password_reset_confirm_short_password_returns_400(self):
        """密码少于8位返回 400"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_generator.make_token(self.user)
        resp = self.client.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "password": "short",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertTrue("error" in resp.json())

    def test_password_reset_request_throttle(self):
        """频繁请求被限流"""
        for _ in range(6):
            self.client.post(
                "/api/auth/password-reset/",
                {
                    "email": "reset@example.com",
                },
            )
        resp = self.client.post(
            "/api/auth/password-reset/",
            {
                "email": "reset@example.com",
            },
        )
        self.assertEqual(resp.status_code, 429)


class PaymentModeViewTest(TestCase):
    """Test payment mode retrieval."""

    def setUp(self):
        self.client = APIClient()

    def test_payment_mode_default_manual(self):
        """默认返回 manual 模式"""
        resp = self.client.get("/api/auth/payment/mode/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["recharge_mode"], "manual")

    def test_payment_mode_after_setting_auto(self):
        """设置为 auto 后返回 auto"""
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        resp = self.client.get("/api/auth/payment/mode/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["recharge_mode"], "auto")


class PaymentCreateViewTest(TestCase):
    """Test payment order creation."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "payuser",
            "pay@example.com",
            "testpass123",
        )

    def _auth(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "payuser",
                "password": "testpass123",
            },
        )
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_payment_create_manual_mode_returns_400(self):
        """手动模式下返回 400"""
        self._auth()
        resp = self.client.post("/api/auth/payment/create/", {"amount": 1000})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("手动充值", resp.json()["error"])

    def test_payment_create_auto_mode_creates_order(self):
        """自动模式创建支付订单"""
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        self._auth()
        resp = self.client.post("/api/auth/payment/create/", {"amount": 2000})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["amount"], 2000)
        self.assertEqual(data["status"], "pending")
        self.assertIsNotNone(data["out_trade_no"])
        self.assertIsNotNone(data["id"])

    def test_payment_create_invalid_amount_returns_400(self):
        """无效金额返回 400"""
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        self._auth()
        resp = self.client.post("/api/auth/payment/create/", {"amount": "abc"})
        self.assertEqual(resp.status_code, 400)

    def test_payment_create_amount_zero_returns_400(self):
        """金额为0返回 400"""
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        self._auth()
        resp = self.client.post("/api/auth/payment/create/", {"amount": 0})
        self.assertEqual(resp.status_code, 400)

    def test_payment_create_unauthenticated_returns_401(self):
        """未认证返回 401"""
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        resp = self.client.post("/api/auth/payment/create/", {"amount": 1000})
        self.assertEqual(resp.status_code, 401)


@override_settings(SECRET_KEY="test-secret-key")
class PaymentNotifyViewTest(TestCase):
    """Test payment notification handling."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        SystemSetting.objects.create(key="recharge_mode", value="auto")
        SystemSetting.objects.create(key="payment_driver", value="simulate")
        self.user = User.objects.create_user(
            "notifyuser",
            "notify@example.com",
            "testpass123",
        )
        self.other_user = User.objects.create_user(
            "otheruser",
            "other@example.com",
            "testpass123",
        )

    def _auth(self, user=None):
        u = user or self.user
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": u.username,
                "password": "testpass123",
            },
        )
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _compute_secret(self):
        return hashlib.sha256(
            (settings.SECRET_KEY + "payment_notify").encode(),
        ).hexdigest()[:16]

    def test_payment_notify_unauthenticated_returns_401(self):
        """未认证返回 401"""
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "out_trade_no": "PAY123",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_payment_notify_wrong_secret_returns_403(self):
        """密钥错误返回 403"""
        self._auth()
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "secret": "wrong-secret",
                "out_trade_no": "PAY123",
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("无效的密钥", resp.json()["error"])

    def test_payment_notify_wrong_user_returns_403(self):
        """非订单用户返回 403"""
        PaymentOrder.objects.create(
            user=self.other_user,
            amount=1000,
            out_trade_no="PAY_OTHER_001",
        )
        secret = self._compute_secret()
        self._auth()
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "secret": secret,
                "out_trade_no": "PAY_OTHER_001",
                "trade_no": "SIM123456",
            },
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("无权操作", resp.json()["error"])

    def test_payment_notify_success(self):
        """成功支付通知增加余额"""
        PaymentOrder.objects.create(
            user=self.user,
            amount=2000,
            out_trade_no="PAY_SUCCESS_001",
        )
        secret = self._compute_secret()
        self._auth()
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "secret": secret,
                "out_trade_no": "PAY_SUCCESS_001",
                "trade_no": "SIM999999",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["success"])

        order = PaymentOrder.objects.get(out_trade_no="PAY_SUCCESS_001")
        self.assertEqual(order.status, "paid")
        self.assertEqual(order.trade_no, "SIM999999")

        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.balance, 2000)

        recharge = Recharge.objects.filter(user=self.user).first()
        self.assertIsNotNone(recharge)
        self.assertEqual(recharge.amount, 2000)
        self.assertEqual(recharge.status, "completed")

    def test_payment_notify_order_not_found_returns_400(self):
        """订单不存在返回 400"""
        secret = self._compute_secret()
        self._auth()
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "secret": secret,
                "out_trade_no": "NONEXISTENT_001",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("不存在", resp.json()["error"])

    def test_payment_notify_order_already_paid_returns_400(self):
        """已支付订单返回 400"""
        PaymentOrder.objects.create(
            user=self.user,
            amount=1000,
            out_trade_no="PAY_DONE_001",
            status="paid",
        )
        secret = self._compute_secret()
        self._auth()
        resp = self.client.post(
            "/api/auth/payment/notify/",
            {
                "secret": secret,
                "out_trade_no": "PAY_DONE_001",
            },
        )
        self.assertEqual(resp.status_code, 400)


class PaymentOrderListViewTest(TestCase):
    """Test payment order listing."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "orderuser",
            "order@example.com",
            "testpass123",
        )

    def _auth(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "orderuser",
                "password": "testpass123",
            },
        )
        token = resp.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_payment_orders_list(self):
        """返回当前用户的支付订单列表"""
        PaymentOrder.objects.create(
            user=self.user,
            amount=1000,
            out_trade_no="ORD_001",
        )
        PaymentOrder.objects.create(
            user=self.user,
            amount=2000,
            out_trade_no="ORD_002",
            status="paid",
        )
        self._auth()
        resp = self.client.get("/api/auth/payment/orders/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 2)
        returned_orders = {o["out_trade_no"] for o in data}
        self.assertIn("ORD_001", returned_orders)
        self.assertIn("ORD_002", returned_orders)

    def test_payment_orders_unauthenticated_returns_401(self):
        """未认证返回 401"""
        resp = self.client.get("/api/auth/payment/orders/")
        self.assertEqual(resp.status_code, 401)


class ThrottleTest(TestCase):
    """Test rate-limiting throttles with default throttle rates."""

    # Default rates: login=10/min, verification_code=1/min, activate=10/min
    # We make more requests than the limit to trigger 429

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            "throttleuser",
            "throttle@example.com",
            "testpass123",
        )

    def test_login_throttle_returns_429(self):
        """频繁登录返回 429（默认限制 10/min）"""
        for _ in range(11):
            self.client.post(
                "/api/auth/login/",
                {
                    "username": "throttleuser",
                    "password": "wrongpass",
                },
            )
        resp = self.client.post(
            "/api/auth/login/",
            {
                "username": "throttleuser",
                "password": "wrongpass",
            },
        )
        self.assertEqual(resp.status_code, 429)

    def test_verification_code_throttle_returns_429(self):
        """频繁发送验证码返回 429（默认限制 1/min）"""
        User.objects.create_user(
            "vcodeuser",
            "vcode@example.com",
            "testpass123",
            is_active=False,
        )
        self.client.post(
            "/api/auth/verification-code/resend/",
            {
                "email": "vcode@example.com",
            },
        )
        resp = self.client.post(
            "/api/auth/verification-code/resend/",
            {
                "email": "vcode@example.com",
            },
        )
        self.assertEqual(resp.status_code, 429)

    def test_activate_throttle_returns_429(self):
        """频繁激活返回 429（默认限制 10/min）"""
        User.objects.create_user(
            "actuser",
            "act@example.com",
            "testpass123",
            is_active=False,
        )
        for _ in range(11):
            self.client.post(
                "/api/auth/activate/",
                {
                    "email": "act@example.com",
                    "code": "111111",
                },
            )
        resp = self.client.post(
            "/api/auth/activate/",
            {
                "email": "act@example.com",
                "code": "111111",
            },
        )
        self.assertEqual(resp.status_code, 429)


class SignalTest(TestCase):
    """Test signals: auto-create Wallet and Subscription on user creation."""

    def test_creates_wallet_and_subscription_on_user_creation(self):
        """用户创建后自动创建 Wallet 和 Subscription"""
        user = User.objects.create_user(
            "signaluser",
            "signal@example.com",
            "testpass123",
        )
        wallet = Wallet.objects.filter(user=user).first()
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet.balance, 0)
        sub = Subscription.objects.filter(user=user).first()
        self.assertIsNotNone(sub)
        self.assertIsNotNone(sub.token)

    def test_signal_only_on_creation(self):
        """更新用户不会重复创建 Wallet 和 Subscription"""
        user = User.objects.create_user(
            "signaluser2",
            "signal2@example.com",
            "testpass123",
        )
        wallet_count = Wallet.objects.filter(user=user).count()
        sub_count = Subscription.objects.filter(user=user).count()
        self.assertEqual(wallet_count, 1)
        self.assertEqual(sub_count, 1)
        user.email = "updated@example.com"
        user.save()
        wallet_count = Wallet.objects.filter(user=user).count()
        sub_count = Subscription.objects.filter(user=user).count()
        self.assertEqual(wallet_count, 1)
        self.assertEqual(sub_count, 1)
