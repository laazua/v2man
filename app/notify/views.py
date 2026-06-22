import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, NotificationRead
from .serializers import NotificationSerializer

logger = logging.getLogger('business')


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(is_active=True)


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = Notification.objects.filter(is_active=True).count()
        read = NotificationRead.objects.filter(user=request.user).count()
        return Response({'unread': max(0, total - read)})


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notification_id = request.data.get('notification_id')
        if notification_id:
            try:
                n = Notification.objects.get(id=notification_id, is_active=True)
                NotificationRead.objects.get_or_create(user=request.user, notification=n)
            except Notification.DoesNotExist:
                pass
        else:
            for n in Notification.objects.filter(is_active=True):
                NotificationRead.objects.get_or_create(user=request.user, notification=n)
        total = Notification.objects.filter(is_active=True).count()
        read = NotificationRead.objects.filter(user=request.user).count()
        return Response({'unread': max(0, total - read)})


class AdminNotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Notification.objects.all()


class AdminNotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Notification.objects.all()
