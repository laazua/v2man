"""Tests for the plans module."""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from nodes.models import Node
from plans.models import Plan
from plans.serializers import PlanSerializer
from users.models import User
from users.wallet import Wallet


class PlanListViewTest(TestCase):
    """Test PlanListView endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.active_plan = Plan.objects.create(
            name='Active Plan', price=5.00,
            traffic_limit=512, duration_days=30, is_active=True,
        )
        self.inactive_plan = Plan.objects.create(
            name='Inactive Plan', price=10.00,
            traffic_limit=1024, duration_days=30, is_active=False,
        )

    def test_list_active_plans(self):
        """公开返回所有启用的套餐"""
        resp = self.client.get('/api/plans/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], 'Active Plan')

    def test_inactive_plans_not_listed(self):
        """未启用套餐不返回"""
        resp = self.client.get('/api/plans/')
        names = [p['name'] for p in resp.data]
        self.assertNotIn('Inactive Plan', names)


class PlanSerializerTest(TestCase):
    """Test PlanSerializer."""

    def setUp(self):
        self.plan = Plan.objects.create(
            name='Test Plan', price=10.00,
            traffic_limit=1024, duration_days=30,
        )

    def test_price_display_format(self):
        """price_display 格式为 ¥{price}"""
        serializer = PlanSerializer(self.plan)
        self.assertEqual(serializer.data['price_display'], '¥10.0')


class PurchaseViewTest(TestCase):
    """Test PurchaseView endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='test123',
        )
        self.plan = Plan.objects.create(
            name='Test Plan', price=10.00,
            traffic_limit=1024, duration_days=30,
        )
        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.balance = 2000
        self.wallet.save()

    def test_purchase_success(self):
        """购买套餐成功，扣余额、更新用户字段"""
        self.client.force_authenticate(self.user)
        with patch('nodes.ssh_utils.sync_users_to_node') as mock_sync:
            mock_sync.return_value = None
            resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['success'])
        self.user.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 1000)  # 2000 - 1000 = 1000
        self.assertEqual(self.user.plan_id, self.plan.id)
        self.assertEqual(self.user.traffic_total, 1024)
        self.assertIsNotNone(self.user.expire_date)

    def test_purchase_insufficient_balance(self):
        """余额不足返回400"""
        self.wallet.balance = 500
        self.wallet.save()
        self.client.force_authenticate(self.user)
        resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('余额不足', resp.data['error'])

    def test_purchase_plan_not_found(self):
        """套餐不存在返回404"""
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/plans/purchase/99999/')
        self.assertEqual(resp.status_code, 404)

    def test_purchase_inactive_plan(self):
        """未启用的套餐不可购买"""
        self.plan.is_active = False
        self.plan.save()
        self.client.force_authenticate(self.user)
        resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 404)

    def test_purchase_unauthenticated(self):
        """未认证用户购买返回非200"""
        self.client.force_authenticate(None)
        resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertNotEqual(resp.status_code, 200)
        self.assertNotEqual(resp.status_code, 201)

    @patch('nodes.ssh_utils.sync_users_to_node')
    def test_purchase_rollback_on_sync_failure(self, mock_sync):
        """节点同步失败自动退款回滚"""
        mock_sync.return_value = 'connection error'
        node = Node.objects.create(
            name='Node1', protocol='vmess',
            address='1.2.3.4', port=443, is_active=True,
        )
        self.plan.nodes.add(node)
        self.client.force_authenticate(self.user)
        resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 502)
        self.user.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 2000)
        self.assertIsNone(self.user.plan_id)
        self.assertEqual(self.user.traffic_total, 0)
        self.assertIsNone(self.user.expire_date)

    @patch('nodes.ssh_utils.sync_users_to_node')
    def test_purchase_rollback_on_sync_exception(self, mock_sync):
        """节点同步抛出异常时自动退款回滚"""
        mock_sync.side_effect = Exception('SSH timeout')
        node = Node.objects.create(
            name='Node1', protocol='vmess',
            address='1.2.3.4', port=443, is_active=True,
        )
        self.plan.nodes.add(node)
        self.client.force_authenticate(self.user)
        resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 502)
        self.user.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 2000)
        self.assertIsNone(self.user.plan_id)

    def test_purchase_admin_no_balance_deduction(self):
        """管理员购买不扣余额"""
        admin = User.objects.create_user(
            username='admin', password='admin123', is_staff=True,
        )
        self.client.force_authenticate(admin)
        with patch('nodes.ssh_utils.sync_users_to_node') as mock_sync:
            mock_sync.return_value = None
            resp = self.client.post(f'/api/plans/purchase/{self.plan.id}/')
        self.assertEqual(resp.status_code, 200)
        admin.refresh_from_db()
        self.assertEqual(admin.plan_id, self.plan.id)
