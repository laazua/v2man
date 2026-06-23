"""通知序列化器。"""

from rest_framework import serializers

from .models import Notification, NotificationRead


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器，包含已读状态。"""
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'is_pinned',
            'is_active', 'created_at', 'is_read',
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_read(self, obj: Notification) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return NotificationRead.objects.filter(
                user=request.user, notification=obj,
            ).exists()
        return False
