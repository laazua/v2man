"""联系反馈模块测试。"""

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from contact.models import ContactMessage
from users.models import User


class ContactMessageListCreateViewTests(TestCase):
    """ContactMessageListCreateView 测试。"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.admin = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
        )
        self.other = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
        )

    def test_get_contact_list_returns_user_messages(self) -> None:
        self.client.force_authenticate(self.user)
        ContactMessage.objects.create(
            user=self.user,
            subject="我的工单",
            message="help",
        )
        ContactMessage.objects.create(
            user=self.other,
            subject="其他人工单",
            message="other",
        )
        resp = self.client.get("/api/contact/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["subject"], "我的工单")

    def test_post_create_ticket(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/contact/",
            {"subject": "问题", "message": "我需要帮助"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.user, self.user)
        self.assertEqual(msg.subject, "问题")

    def test_unauthenticated_returns_401(self) -> None:
        resp = self.client.get("/api/contact/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post(
            "/api/contact/",
            {"message": "test"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_only_sees_own_messages(self) -> None:
        ContactMessage.objects.create(
            user=self.user,
            subject="我的",
            message="a",
        )
        ContactMessage.objects.create(
            user=self.other,
            subject="他人的",
            message="b",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/contact/")
        subjects = [item["subject"] for item in resp.data]
        self.assertIn("我的", subjects)
        self.assertNotIn("他人的", subjects)

    def test_admin_only_sees_own_messages_in_user_view(self) -> None:
        ContactMessage.objects.create(
            user=self.admin,
            subject="管理员工单",
            message="x",
        )
        ContactMessage.objects.create(
            user=self.other,
            subject="普通用户",
            message="y",
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/contact/")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["subject"], "管理员工单")


class ContactMessageReplyViewTests(TestCase):
    """ContactMessageReplyView 测试。"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.other = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
        )
        self.ticket = ContactMessage.objects.create(
            user=self.user,
            subject="工单",
            message="问题",
        )

    def test_user_reply_own_ticket(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/contact/{self.ticket.id}/reply/",
            {"message": "我的回复"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ContactMessage.objects.filter(parent=self.ticket).count(),
            1,
        )
        reply = ContactMessage.objects.get(parent=self.ticket)
        self.assertEqual(reply.message, "我的回复")
        self.assertFalse(reply.is_admin)

    def test_reply_updates_status_to_pending(self) -> None:
        self.ticket.status = "replied"
        self.ticket.save(update_fields=["status"])
        self.client.force_authenticate(self.user)
        self.client.post(
            f"/api/contact/{self.ticket.id}/reply/",
            {"message": "回复"},
            format="json",
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "pending")

    def test_reply_other_user_ticket_returns_404(self) -> None:
        self.client.force_authenticate(self.other)
        resp = self.client.post(
            f"/api/contact/{self.ticket.id}/reply/",
            {"message": "别人的工单"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_message_returns_400(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            f"/api/contact/{self.ticket.id}/reply/",
            {"message": "   "},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_ticket_returns_404(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/contact/999/reply/",
            {"message": "test"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ContactUnreadViewTests(TestCase):
    """ContactUnreadView 测试。"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

    def test_unread_count_zero(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/contact/unread-count/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["unread"], 0)

    def test_unread_count_with_replied_tickets(self) -> None:
        self.client.force_authenticate(self.user)
        ContactMessage.objects.create(
            user=self.user,
            subject="已回复",
            message="a",
            status="replied",
        )
        ContactMessage.objects.create(
            user=self.user,
            subject="待回复",
            message="b",
            status="pending",
        )
        resp = self.client.get("/api/contact/unread-count/")
        self.assertEqual(resp.data["unread"], 1)

    def test_unread_count_with_after_filter(self) -> None:
        self.client.force_authenticate(self.user)
        msg = ContactMessage.objects.create(
            user=self.user,
            subject="旧",
            message="x",
            status="replied",
            replied_at=timezone.now(),
        )
        resp = self.client.get(
            "/api/contact/unread-count/",
            {"after": timezone.now()},
        )
        self.assertEqual(resp.data["unread"], 0)


class AdminContactViewSetTests(TestCase):
    """AdminContactViewSet 测试。"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            password="adminpass123",
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.ticket = ContactMessage.objects.create(
            user=self.user,
            subject="求助",
            message="help",
            status="pending",
        )

    def test_list_all_tickets(self) -> None:
        ContactMessage.objects.create(
            user=self.user,
            subject="第二个",
            message="more",
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/admin/contact/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_list_requires_admin(self) -> None:
        self.client.force_authenticate(self.user)
        resp = self.client.get("/api/admin/contact/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_reply(self) -> None:
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f"/api/admin/contact/{self.ticket.id}/reply/",
            {"message": "管理员回复"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "replied")
        self.assertIsNotNone(self.ticket.replied_at)
        reply = ContactMessage.objects.get(parent=self.ticket)
        self.assertTrue(reply.is_admin)

    def test_admin_reply_empty_message(self) -> None:
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f"/api/admin/contact/{self.ticket.id}/reply/",
            {"message": ""},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pending_count(self) -> None:
        ContactMessage.objects.create(
            user=self.user,
            subject="另一个",
            message="x",
            status="pending",
        )
        ContactMessage.objects.create(
            user=self.user,
            subject="已回复",
            message="y",
            status="replied",
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/admin/contact/pending_count/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["pending"], 2)

    def test_toggle_visibility(self) -> None:
        self.client.force_authenticate(self.admin)
        reply = ContactMessage.objects.create(
            parent=self.ticket,
            user=self.user,
            message="回复",
            is_admin=True,
            visible_to_user=True,
        )
        resp = self.client.post(
            f"/api/admin/contact/{self.ticket.id}/toggle_visibility/",
            {"reply_id": reply.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["visible_to_user"])
        reply.refresh_from_db()
        self.assertFalse(reply.visible_to_user)

    def test_toggle_visibility_nonexistent_reply(self) -> None:
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f"/api/admin/contact/{self.ticket.id}/toggle_visibility/",
            {"reply_id": 999},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
