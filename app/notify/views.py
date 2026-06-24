"""通知公告相关 API 视图。"""

import logging
from typing import Optional

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationRead
from .serializers import NotificationSerializer

logger = logging.getLogger("business")


class NotificationListView(generics.ListAPIView):
    """用户可见的通知列表。"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(is_active=True)


class UnreadCountView(APIView):
    """未读通知数量。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        total = Notification.objects.filter(is_active=True).count()
        read = NotificationRead.objects.filter(user=request.user).count()
        return Response({"unread": max(0, total - read)})


class MarkReadView(APIView):
    """标记通知为已读。"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        notification_id: Optional[str] = request.data.get(
            "notification_id",
        )
        if notification_id:
            try:
                n = Notification.objects.get(
                    id=notification_id,
                    is_active=True,
                )
                NotificationRead.objects.get_or_create(
                    user=request.user,
                    notification=n,
                )
            except Notification.DoesNotExist:
                pass
        else:
            for n in Notification.objects.filter(is_active=True):
                NotificationRead.objects.get_or_create(
                    user=request.user,
                    notification=n,
                )
        total = Notification.objects.filter(is_active=True).count()
        read = NotificationRead.objects.filter(user=request.user).count()
        return Response({"unread": max(0, total - read)})


class AdminNotificationListCreateView(generics.ListCreateAPIView):
    """管理员管理通知（列表 + 创建）。"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Notification.objects.all()


class AdminNotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """管理员管理通知（详情 + 修改 + 删除）。"""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Notification.objects.all()
