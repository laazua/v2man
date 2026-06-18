from rest_framework import serializers
from .models import Notification, NotificationRead


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'content', 'is_pinned', 'is_active', 'created_at', 'is_read']
        read_only_fields = ['id', 'created_at']

    def get_is_read(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return NotificationRead.objects.filter(user=user, notification=obj).exists()
        return False
