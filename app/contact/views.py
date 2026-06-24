"""用户联系反馈相关 API 视图。"""

import logging

from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import ContactMessage
from .serializers import ContactMessageSerializer

logger = logging.getLogger("business")


class ContactMessageListCreateView(generics.ListCreateAPIView):
    """用户创建和查看工单。"""

    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContactMessage.objects.filter(
            user=self.request.user,
            parent=None,
        )

    def perform_create(self, serializer) -> None:
        instance = serializer.save(user=self.request.user)
        logger.info(
            "用户创建工单: user_id=%s message_id=%s",
            self.request.user.id,
            instance.id,
        )


class ContactMessageReplyView(generics.GenericAPIView):
    """用户回复工单。"""

    permission_classes = [permissions.IsAuthenticated]

    def post(  # type: ignore[override]
        self,
        request: Request,
        pk: int = None,
    ) -> Response:
        try:
            root = ContactMessage.objects.get(
                pk=pk,
                parent=None,
                user=request.user,
            )
        except ContactMessage.DoesNotExist:
            return Response({"error": "消息不存在"}, status=404)

        text = request.data.get("message", "").strip()
        if not text:
            return Response(
                {"error": "回复内容不能为空"},
                status=400,
            )

        ContactMessage.objects.create(
            parent=root,
            user=request.user,
            message=text,
            is_admin=False,
        )
        root.status = "pending"
        root.save(update_fields=["status"])

        logger.info(
            "用户回复工单: user_id=%s message_id=%s",
            request.user.id,
            root.id,
        )
        return Response({"status": "ok"}, status=201)


class ContactUnreadView(generics.GenericAPIView):
    """用户未读回复数量。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        after = request.GET.get("after")
        qs = ContactMessage.objects.filter(
            user=request.user,
            parent=None,
            status="replied",
        )
        if after:
            qs = qs.filter(replied_at__gt=after)
        return Response({"unread": qs.count()})


class AdminContactViewSet(viewsets.ReadOnlyModelViewSet):
    """管理员查看和管理工单。"""

    queryset = ContactMessage.objects.filter(
        parent=None,
    ).select_related("user")
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        from .serializers import AdminContactMessageSerializer

        return AdminContactMessageSerializer

    @action(detail=False, methods=["get"])
    def pending_count(  # type: ignore[override]
        self,
        request: Request,
    ) -> Response:
        count = ContactMessage.objects.filter(
            parent=None,
            status="pending",
        ).count()
        return Response({"pending": count})

    @action(detail=True, methods=["post"])
    def reply(  # type: ignore[override]
        self,
        request: Request,
        pk: int = None,
    ) -> Response:
        root = self.get_object()
        text = request.data.get("message", "").strip()
        if not text:
            return Response(
                {"error": "回复内容不能为空"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ContactMessage.objects.create(
            parent=root,
            user=root.user,
            message=text,
            is_admin=True,
        )
        root.status = "replied"
        root.replied_at = timezone.now()
        root.save(update_fields=["status", "replied_at"])

        logger.info(
            "管理员回复工单: admin_id=%s message_id=%s",
            request.user.id,
            root.id,
        )
        return Response({"status": "ok", "replied_at": root.replied_at})

    @action(detail=True, methods=["post"])
    def toggle_visibility(  # type: ignore[override]
        self,
        request: Request,
        pk: int = None,
    ) -> Response:
        root = self.get_object()
        reply_id = request.data.get("reply_id")
        try:
            reply = root.replies.get(pk=reply_id)
        except ContactMessage.DoesNotExist:
            return Response({"error": "回复不存在"}, status=404)
        reply.visible_to_user = not reply.visible_to_user
        reply.save(update_fields=["visible_to_user"])
        return Response(
            {
                "status": "ok",
                "reply_id": reply.id,
                "visible_to_user": reply.visible_to_user,
            }
        )
