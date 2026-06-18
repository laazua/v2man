from rest_framework import serializers

from .models import ContactMessage


class ReplySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    visible_to_user = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ContactMessageSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ContactMessage
        fields = ["id", "subject", "message", "status", "replies", "replied_at", "created_at"]
        read_only_fields = ["id", "status", "replies", "replied_at", "created_at"]

    def get_replies(self, obj):
        replies = obj.replies.filter(visible_to_user=True).order_by("created_at")
        return ReplySerializer(replies, many=True).data


class AdminContactMessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ContactMessage
        fields = ["id", "username", "subject", "message", "status", "replies", "replied_at", "created_at"]
        read_only_fields = fields

    def get_replies(self, obj):
        replies = obj.replies.all().order_by("created_at")
        return ReplySerializer(replies, many=True).data
