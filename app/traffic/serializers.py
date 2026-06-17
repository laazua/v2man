from rest_framework import serializers
from .models import TrafficLog


class TrafficRecordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    upload_bytes = serializers.IntegerField(min_value=0)
    download_bytes = serializers.IntegerField(min_value=0)
    node_name = serializers.CharField(required=False, allow_blank=True, default='')


class TrafficLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLog
        fields = ['upload_bytes', 'download_bytes', 'recorded_at', 'node_name']
