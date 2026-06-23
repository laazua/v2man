"""Serializers for the nodes app."""

from rest_framework import serializers

from .models import Node


class NodePublicSerializer(serializers.ModelSerializer):
    """Public serializer exposing limited node fields."""

    class Meta:
        model = Node
        fields = [
            "id", "name", "protocol", "address", "port",
            "sort_order", "is_active",
        ]


class NodeSerializer(serializers.ModelSerializer):
    """Full serializer including SSH configuration fields."""

    ssh_configured = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = [
            "id", "name", "protocol", "address", "port", "config",
            "config_path", "reload_cmd", "sort_order", "is_active",
            "ssh_host", "ssh_port", "ssh_user", "ssh_key",
            "ssh_password", "ssh_configured", "deployed_at",
        ]
        extra_kwargs = {
            "ssh_key": {"write_only": True},
            "ssh_password": {"write_only": True},
        }

    def get_ssh_configured(self, obj: Node) -> bool:
        """Check if SSH credentials are configured."""
        return bool(obj.ssh_key or obj.ssh_password)