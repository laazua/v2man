"""Tests for the traffic module."""

from django.test import TestCase
from rest_framework.test import APIClient

from traffic.models import TrafficLog
from users.models import User


class TrafficRecordViewTest(TestCase):
    """Test TrafficRecordView endpoint."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123', is_staff=True,
        )
        self.user = User.objects.create_user(
            username='testuser', password='test123',
            traffic_used=0,
        )
        self.client = APIClient()

    def test_admin_record_traffic(self):
        """管理员录入流量，累加到 user.traffic_used"""
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/traffic/record/', {
            'user_id': self.user.id,
            'upload_bytes': 1048576,
            'download_bytes': 2097152,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['success'])
        self.user.refresh_from_db()
        # (1048576 + 2097152) / 1048576 = 3, max(1, 3) = 3
        self.assertEqual(self.user.traffic_used, 3)

    def test_non_admin_cannot_record_traffic(self):
        """非管理员录入流量返回403"""
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/traffic/record/', {
            'user_id': self.user.id,
            'upload_bytes': 100,
            'download_bytes': 100,
        })
        self.assertEqual(resp.status_code, 403)

    def test_record_missing_required_fields(self):
        """缺少必填字段返回400"""
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/traffic/record/', {})
        self.assertEqual(resp.status_code, 400)


class TrafficStatsViewTest(TestCase):
    """Test TrafficStatsView endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test123',
        )
        self.client = APIClient()
        TrafficLog.objects.create(
            user=self.user, upload_bytes=1048576, download_bytes=0,
        )
        TrafficLog.objects.create(
            user=self.user, upload_bytes=0, download_bytes=2097152,
        )

    def test_user_traffic_stats(self):
        """返回当前用户流量明细（按日汇总）"""
        self.client.force_authenticate(self.user)
        resp = self.client.get('/api/traffic/stats/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('daily', resp.data)
        self.assertIn('total_upload_mb', resp.data)
        self.assertIn('total_download_mb', resp.data)
        # upload: 1048576 / 1048576 = 1 MB
        # download: 2097152 / 1048576 = 2 MB
        self.assertEqual(resp.data['total_upload_mb'], 1.0)
        self.assertEqual(resp.data['total_download_mb'], 2.0)
        self.assertEqual(len(resp.data['daily']), 1)
