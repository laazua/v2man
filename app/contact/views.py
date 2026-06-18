from django.utils import timezone
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ContactMessage.objects.filter(user=self.request.user, parent=None)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactMessageReplyView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        try:
            root = ContactMessage.objects.get(pk=pk, parent=None, user=request.user)
        except ContactMessage.DoesNotExist:
            return Response({"error": "消息不存在"}, status=404)

        text = request.data.get("message", "").strip()
        if not text:
            return Response({"error": "回复内容不能为空"}, status=400)

        ContactMessage.objects.create(
            parent=root,
            user=request.user,
            message=text,
            is_admin=False,
        )
        root.status = "pending"
        root.save(update_fields=["status"])

        return Response({"status": "ok"}, status=201)


class ContactUnreadView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        after = request.GET.get("after")
        qs = ContactMessage.objects.filter(user=request.user, parent=None, status="replied")
        if after:
            qs = qs.filter(replied_at__gt=after)
        return Response({"unread": qs.count()})


class AdminContactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContactMessage.objects.filter(parent=None).select_related("user")
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        from .serializers import AdminContactMessageSerializer
        return AdminContactMessageSerializer

    @action(detail=False, methods=["get"])
    def pending_count(self, request):
        count = ContactMessage.objects.filter(parent=None, status="pending").count()
        return Response({"pending": count})

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        root = self.get_object()
        text = request.data.get("message", "").strip()
        if not text:
            return Response({"error": "回复内容不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        ContactMessage.objects.create(
            parent=root,
            user=root.user,
            message=text,
            is_admin=True,
        )
        root.status = "replied"
        root.replied_at = timezone.now()
        root.save(update_fields=["status", "replied_at"])

        return Response({"status": "ok", "replied_at": root.replied_at})

    @action(detail=True, methods=["post"])
    def toggle_visibility(self, request, pk=None):
        root = self.get_object()
        reply_id = request.data.get("reply_id")
        try:
            reply = root.replies.get(pk=reply_id)
        except ContactMessage.DoesNotExist:
            return Response({"error": "回复不存在"}, status=404)
        reply.visible_to_user = not reply.visible_to_user
        reply.save(update_fields=["visible_to_user"])
        return Response({
            "status": "ok",
            "reply_id": reply.id,
            "visible_to_user": reply.visible_to_user,
        })
