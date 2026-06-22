from rest_framework import serializers
from .models import Node


class NodePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ["id", "name", "protocol", "address", "port",
                  "sort_order", "is_active"]


class NodeSerializer(serializers.ModelSerializer):
    ssh_configured = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = ["id", "name", "protocol", "address", "port", "config",
                  "config_path", "reload_cmd", "sort_order", "is_active",
                  "ssh_host", "ssh_port", "ssh_user", "ssh_key", "ssh_password",
                  "ssh_configured"]
        extra_kwargs = {
            "ssh_key": {"write_only": True},
            "ssh_password": {"write_only": True},
            "ssh_host": {"write_only": True},
            "ssh_port": {"write_only": True},
            "ssh_user": {"write_only": True},
            "config_path": {"write_only": True},
            "reload_cmd": {"write_only": True},
            "config": {"write_only": True},
        }

    def get_ssh_configured(self, obj) -> bool:
        return bool(obj.ssh_key or obj.ssh_password)