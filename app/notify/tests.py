"""通知公告测试。"""

from django.test import TestCase
from rest_framework.test import APIClient

from notify.models import Notification, NotificationRead
from users.models import User


class NotificationListViewTest(TestCase):
    """通知列表测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="notify-user",
            password="test123",
        )
        self.client.force_authenticate(user=self.user)
        self.notification = Notification.objects.create(
            title="Test Notification",
            content="Test content",
        )
        Notification.objects.create(
            title="Inactive",
            content="Should not appear",
            is_active=False,
        )

    def test_list_active_notifications(self):
        resp = self.client.get("/api/notifications/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["title"], "Test Notification")

    def test_is_read_field_present(self):
        resp = self.client.get("/api/notifications/")
        self.assertIn("is_read", resp.data[0])

    def test_is_read_false_by_default(self):
        resp = self.client.get("/api/notifications/")
        self.assertFalse(resp.data[0]["is_read"])

    def test_is_read_true_after_marking(self):
        NotificationRead.objects.create(
            user=self.user,
            notification=self.notification,
        )
        resp = self.client.get("/api/notifications/")
        self.assertTrue(resp.data[0]["is_read"])


class UnreadCountViewTest(TestCase):
    """未读通知数量测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="count-user",
            password="test123",
        )
        self.client.force_authenticate(user=self.user)

    def test_unread_count_all_unread(self):
        Notification.objects.create(title="N1", content="C1")
        Notification.objects.create(title="N2", content="C2")
        resp = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.data["unread"], 2)

    def test_unread_count_some_read(self):
        n1 = Notification.objects.create(title="N1", content="C1")
        Notification.objects.create(title="N2", content="C2")
        NotificationRead.objects.create(
            user=self.user,
            notification=n1,
        )
        resp = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.data["unread"], 1)

    def test_unread_count_zero(self):
        resp = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(resp.data["unread"], 0)


class MarkReadViewTest(TestCase):
    """标记已读测试。"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="mark-user",
            password="test123",
        )
        self.client.force_authenticate(user=self.user)
        self.n1 = Notification.objects.create(title="N1", content="C1")
        self.n2 = Notification.objects.create(title="N2", content="C2")

    def test_mark_single_read(self):
        resp = self.client.post(
            "/api/notifications/mark-read/",
            {"notification_id": self.n1.id},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            NotificationRead.objects.filter(
                user=self.user,
                notification=self.n1,
            ).exists(),
        )
        self.assertFalse(
            NotificationRead.objects.filter(
                user=self.user,
                notification=self.n2,
            ).exists(),
        )

    def test_mark_all_read(self):
        resp = self.client.post("/api/notifications/mark-read/", {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            NotificationRead.objects.filter(
                user=self.user,
            ).count(),
            2,
        )

    def test_mark_single_twice_no_error(self):
        self.client.post(
            "/api/notifications/mark-read/",
            {"notification_id": self.n1.id},
        )
        resp = self.client.post(
            "/api/notifications/mark-read/",
            {"notification_id": self.n1.id},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            NotificationRead.objects.filter(
                user=self.user,
                notification=self.n1,
            ).count(),
            1,
        )

    def test_mark_nonexistent_notification(self):
        resp = self.client.post(
            "/api/notifications/mark-read/",
            {"notification_id": 99999},
        )
        self.assertEqual(resp.status_code, 200)


class AdminNotificationListCreateViewTest(TestCase):
    """管理员通知管理（列表+创建）测试。"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="notify-admin",
            password="test123",
        )
        self.user = User.objects.create_user(
            username="normal-user",
            password="test123",
        )

    def test_admin_list_notifications(self):
        Notification.objects.create(title="N1", content="C1")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/admin/notifications/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_admin_create_notification(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            "/api/admin/notifications/",
            {"title": "New Notif", "content": "New content"},
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)

    def test_non_admin_cannot_access(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/admin/notifications/")
        self.assertEqual(resp.status_code, 403)

    def test_non_admin_cannot_create(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/admin/notifications/",
            {"title": "Hack", "content": "Hack content"},
        )
        self.assertEqual(resp.status_code, 403)


class AdminNotificationDetailViewTest(TestCase):
    """管理员通知详情管理测试。"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="notify-admin2",
            password="test123",
        )
        self.client.force_authenticate(user=self.admin)
        self.notification = Notification.objects.create(
            title="Detail Test",
            content="Detail content",
        )

    def test_get_detail(self):
        resp = self.client.get(
            f"/api/admin/notifications/{self.notification.id}/",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["title"], "Detail Test")

    def test_update(self):
        resp = self.client.put(
            f"/api/admin/notifications/{self.notification.id}/",
            {"title": "Updated", "content": "Updated content"},
        )
        self.assertEqual(resp.status_code, 200)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.title, "Updated")

    def test_delete(self):
        resp = self.client.delete(
            f"/api/admin/notifications/{self.notification.id}/",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(
            Notification.objects.filter(
                id=self.notification.id,
            ).exists(),
        )

    def test_404_for_nonexistent(self):
        resp = self.client.get("/api/admin/notifications/99999/")
        self.assertEqual(resp.status_code, 404)
