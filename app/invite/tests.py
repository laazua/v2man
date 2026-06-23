"""邀请码、推广、提现测试。"""

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User
from users.wallet import Wallet
from invite.models import InviteCode, Referral, Withdrawal, SystemSetting


class GenerateInviteCodeViewTest(TestCase):
    """生成邀请码测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inviter", password="test123",
        )

    def test_generate_code(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post("/api/invite/codes/generate/")
        self.assertEqual(resp.status_code, 201)
        self.assertIn("code", resp.data)
        self.assertTrue(
            InviteCode.objects.filter(owner=self.user).exists(),
        )

    def test_unauthenticated_returns_401(self):
        resp = self.client.post("/api/invite/codes/generate/")
        self.assertEqual(resp.status_code, 401)


class ListInviteCodesViewTest(TestCase):
    """邀请码列表测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inviter2", password="test123",
        )
        self.client.force_authenticate(user=self.user)
        InviteCode.objects.create(owner=self.user)
        InviteCode.objects.create(owner=self.user)

    def test_list_codes(self):
        resp = self.client.get("/api/invite/codes/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_other_user_codes_not_included(self):
        other = User.objects.create_user(
            username="other", password="test123",
        )
        InviteCode.objects.create(owner=other)
        resp = self.client.get("/api/invite/codes/")
        self.assertEqual(len(resp.data), 2)


class ListReferralsViewTest(TestCase):
    """推广记录测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="inviter3", password="test123",
        )
        self.client.force_authenticate(user=self.user)
        self.invited = User.objects.create_user(
            username="invited1", password="test123",
        )
        code = InviteCode.objects.create(owner=self.user)
        Referral.objects.create(
            inviter=self.user, invited=self.invited,
            invite_code=code, earned=500,
        )

    def test_list_referrals(self):
        resp = self.client.get("/api/invite/referrals/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertIn("earned", resp.data[0])
        self.assertEqual(resp.data[0]["earned"], 500)


class EarningsViewTest(TestCase):
    """收益概览测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="earner", password="test123",
        )
        self.client.force_authenticate(user=self.user)

    def test_earnings_zero(self):
        resp = self.client.get("/api/invite/earnings/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_earned"], 0)
        self.assertEqual(resp.data["total_referees"], 0)

    def test_earnings_with_referrals(self):
        invited = User.objects.create_user(
            username="ref", password="test123",
        )
        Referral.objects.create(
            inviter=self.user, invited=invited, earned=1000,
        )
        resp = self.client.get("/api/invite/earnings/")
        self.assertEqual(resp.data["total_earned"], 1000)
        self.assertEqual(resp.data["total_referees"], 1)
        self.assertEqual(resp.data["percentage"], 20)


class CreateWithdrawalViewTest(TestCase):
    """创建提现测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="withdrawer", password="test123",
        )
        self.client.force_authenticate(user=self.user)
        self.wallet = Wallet.objects.get(user=self.user)

    def test_create_withdrawal_success(self):
        self.wallet.balance = 10000
        self.wallet.save()
        resp = self.client.post(
            "/api/invite/withdrawals/create/",
            {"amount": 5000},
        )
        self.assertEqual(resp.status_code, 201)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 5000)
        self.assertTrue(
            Withdrawal.objects.filter(
                user=self.user, amount=5000,
            ).exists(),
        )

    def test_insufficient_balance(self):
        self.wallet.balance = 1000
        self.wallet.save()
        resp = self.client.post(
            "/api/invite/withdrawals/create/",
            {"amount": 5000},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("余额不足", str(resp.data["error"]))

    def test_below_minimum_amount(self):
        self.wallet.balance = 50000
        self.wallet.save()
        resp = self.client.post(
            "/api/invite/withdrawals/create/",
            {"amount": 100},
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_amount(self):
        resp = self.client.post(
            "/api/invite/withdrawals/create/",
            {"amount": "not-a-number"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_negative_amount(self):
        resp = self.client.post(
            "/api/invite/withdrawals/create/",
            {"amount": -100},
        )
        self.assertEqual(resp.status_code, 400)


class ListWithdrawalsViewTest(TestCase):
    """提现记录测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="wd-user", password="test123",
        )
        self.client.force_authenticate(user=self.user)
        Withdrawal.objects.create(user=self.user, amount=3000)
        Withdrawal.objects.create(user=self.user, amount=5000)

    def test_list_withdrawals(self):
        resp = self.client.get("/api/invite/withdrawals/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)


class SettingsViewTest(TestCase):
    """管理员推广设置测试。"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin", password="test123", is_staff=True,
        )
        self.user = User.objects.create_user(
            username="normal", password="test123",
        )

    def test_admin_get_settings(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/admin/invite/settings/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("referral_percentage", resp.data)
        self.assertIn("withdrawal_min", resp.data)

    def test_admin_update_settings(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put(
            "/api/admin/invite/settings/",
            {
                "referral_percentage": "30",
                "withdrawal_min": "5000",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            SystemSetting.get("referral_percentage"), "30",
        )
        self.assertEqual(
            SystemSetting.get_int("withdrawal_min"), 5000,
        )

    def test_non_admin_cannot_access(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/admin/invite/settings/")
        self.assertEqual(resp.status_code, 403)

    def test_invalid_key_rejected(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put(
            "/api/admin/invite/settings/",
            {"invalid_key": "100"},
        )
        self.assertEqual(resp.status_code, 400)


class AdminWithdrawalListViewTest(TestCase):
    """管理员提现列表测试。"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin2", password="test123",
        )
        self.client.force_authenticate(user=self.admin)
        user = User.objects.create_user(
            username="wd-user2", password="test123",
        )
        Withdrawal.objects.create(user=user, amount=5000)

    def test_list_all_withdrawals(self):
        resp = self.client.get("/api/admin/invite/withdrawals/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)


class AdminWithdrawalActionViewTest(TestCase):
    """管理员审核提现测试。"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin3", password="test123",
        )
        self.client.force_authenticate(user=self.admin)
        self.user = User.objects.create_user(
            username="wd-user3", password="test123",
        )
        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.balance = 10000
        self.wallet.save()
        self.withdrawal = Withdrawal.objects.create(
            user=self.user, amount=5000,
        )

    def test_approve_withdrawal(self):
        resp = self.client.post(
            f"/api/admin/invite/withdrawals/"
            f"{self.withdrawal.id}/action/",
            {"action": "approve"},
        )
        self.assertEqual(resp.status_code, 200)
        self.withdrawal.refresh_from_db()
        self.assertEqual(self.withdrawal.status, "approved")

    def test_reject_withdrawal_refunds(self):
        resp = self.client.post(
            f"/api/admin/invite/withdrawals/"
            f"{self.withdrawal.id}/action/",
            {"action": "reject"},
        )
        self.assertEqual(resp.status_code, 200)
        self.withdrawal.refresh_from_db()
        self.assertEqual(self.withdrawal.status, "rejected")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 15000)

    def test_invalid_action(self):
        resp = self.client.post(
            f"/api/admin/invite/withdrawals/"
            f"{self.withdrawal.id}/action/",
            {"action": "invalid"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_already_processed(self):
        self.withdrawal.status = "approved"
        self.withdrawal.save()
        resp = self.client.post(
            f"/api/admin/invite/withdrawals/"
            f"{self.withdrawal.id}/action/",
            {"action": "reject"},
        )
        self.assertEqual(resp.status_code, 404)
