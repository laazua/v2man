"""Tests for admin user and recharge management views."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from nodes.models import Node
from plans.models import Plan
from users.models import User
from users.wallet import Recharge, Wallet


class AdminUserViewSetTest(TestCase):
    """Test AdminUserViewSet endpoints."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', is_staff=True,
        )
        self.user = User.objects.create_user(
            username='testuser', password='test123',
        )
        self.client = APIClient()
        self.plan = Plan.objects.create(
            name='Test Plan', price=10.00,
            traffic_limit=1024, duration_days=30,
        )

    def test_admin_list_users(self):
        """管理员可以获取用户列表"""
        self.client.force_authenticate(self.admin)
        resp = self.client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_non_admin_cannot_list_users(self):
        """非管理员访问用户列表返回403"""
        self.client.force_authenticate(self.user)
        resp = self.client.get('/api/admin/users/')
        self.assertEqual(resp.status_code, 403)

    def test_admin_retrieve_user(self):
        """管理员可以获取单个用户"""
        self.client.force_authenticate(self.admin)
        resp = self.client.get(f'/api/admin/users/{self.user.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'testuser')

    @patch('users.admin_views.sync_users_to_node')
    def test_update_user_plan_and_fields(self, mock_sync):
        """管理员更新用户套餐和字段"""
        mock_sync.return_value = None
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(
            f'/api/admin/users/{self.user.id}/update_user/',
            {'plan_id': self.plan.id, 'email': 'new@test.com'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_id, self.plan.id)
        self.assertEqual(self.user.email, 'new@test.com')

    @patch('users.admin_views.sync_users_to_node')
    def test_update_user_password(self, mock_sync):
        """管理员更新用户密码"""
        mock_sync.return_value = None
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(
            f'/api/admin/users/{self.user.id}/update_user/',
            {'password': 'newpass123'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    @patch('users.admin_views.sync_users_to_node')
    def test_update_user_traffic_and_expire(self, mock_sync):
        """管理员更新用户流量和到期时间"""
        mock_sync.return_value = None
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(
            f'/api/admin/users/{self.user.id}/update_user/',
            {'traffic_used': 500, 'traffic_total': 1024, 'is_active': False},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.traffic_used, 500)
        self.assertEqual(self.user.traffic_total, 1024)
        self.assertFalse(self.user.is_active)

    def test_update_user_plan_not_found(self):
        """更新用户套餐时套餐不存在返回400"""
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(
            f'/api/admin/users/{self.user.id}/update_user/',
            {'plan_id': 99999},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_top_up_user(self):
        """管理员为用户充值"""
        self.client.force_authenticate(self.admin)
        wallet = Wallet.objects.get(user=self.user)
        wallet.balance = 0
        wallet.save()
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/top_up/',
            {'amount': 1000},
        )
        self.assertEqual(resp.status_code, 200)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 1000)

    def test_top_up_invalid_amount(self):
        """管理员充值金额不合法返回400"""
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/top_up/',
            {'amount': -1},
        )
        self.assertEqual(resp.status_code, 400)

    @patch('users.admin_views.sync_users_to_node')
    def test_invalidate_subscription(self, mock_sync):
        """管理员失效订阅重置UUID"""
        mock_sync.return_value = None
        self.client.force_authenticate(self.admin)
        old_uuid = str(self.user.uuid)
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/invalidate_subscription/',
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(str(self.user.uuid), old_uuid)

    def test_destroy_user(self):
        """管理员删除用户"""
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/destroy_user/',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_non_admin_cannot_destroy_user(self):
        """非管理员删除用户返回403"""
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/destroy_user/',
        )
        self.assertEqual(resp.status_code, 403)

    @patch('users.admin_views.sync_users_to_node')
    def test_sync_config(self, mock_sync):
        """管理员同步配置到节点"""
        mock_sync.return_value = None
        self.user.plan = self.plan
        self.user.save()
        node = Node.objects.create(
            name='Test Node', protocol='vmess',
            address='1.2.3.4', port=443, is_active=True,
        )
        self.plan.nodes.add(node)
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/admin/users/{self.user.id}/sync_config/',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['success'])


class AdminRechargeViewSetTest(TestCase):
    """Test AdminRechargeViewSet endpoints."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', is_staff=True,
        )
        self.user = User.objects.create_user(
            username='testuser', password='test123',
        )
        self.client = APIClient()
        self.recharge = Recharge.objects.create(
            user=self.user, amount=1000, status='pending',
        )

    def test_list_recharges(self):
        """管理员查看充值记录列表"""
        self.client.force_authenticate(self.admin)
        resp = self.client.get('/api/admin/recharges/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_confirm_recharge(self):
        """管理员确认充值，余额增加"""
        self.client.force_authenticate(self.admin)
        wallet = Wallet.objects.get(user=self.user)
        wallet.balance = 0
        wallet.save()
        resp = self.client.post(
            f'/api/admin/recharges/{self.recharge.id}/confirm/',
        )
        self.assertEqual(resp.status_code, 200)
        self.recharge.refresh_from_db()
        self.assertEqual(self.recharge.status, 'completed')
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 1000)

    def test_confirm_recharge_already_processed(self):
        """确认已处理的充值返回400"""
        self.client.force_authenticate(self.admin)
        self.recharge.status = 'completed'
        self.recharge.save()
        resp = self.client.post(
            f'/api/admin/recharges/{self.recharge.id}/confirm/',
        )
        self.assertEqual(resp.status_code, 400)

    def test_reject_recharge(self):
        """管理员拒绝充值"""
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/admin/recharges/{self.recharge.id}/reject/',
            {'remark': 'fraud'},
        )
        self.assertEqual(resp.status_code, 200)
        self.recharge.refresh_from_db()
        self.assertEqual(self.recharge.status, 'failed')
        self.assertEqual(self.recharge.admin_remark, 'fraud')

    def test_reject_recharge_already_processed(self):
        """拒绝已处理的充值返回400"""
        self.client.force_authenticate(self.admin)
        self.recharge.status = 'failed'
        self.recharge.save()
        resp = self.client.post(
            f'/api/admin/recharges/{self.recharge.id}/reject/',
        )
        self.assertEqual(resp.status_code, 400)
