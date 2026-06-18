from rest_framework import serializers
from .models import Node


class NodeSerializer(serializers.ModelSerializer):
    ssh_configured = serializers.SerializerMethodField()

    class Meta:
        model = Node
        fields = ["id", "name", "protocol", "address", "port", "config",
                  "config_path", "reload_cmd", "sort_order", "is_active",
                  "ssh_host", "ssh_port", "ssh_user", "ssh_key", "ssh_password",
                  "ssh_configured"]
        extra_kwargs = {
            "ssh_key": {"write_only": True, "required": False, "allow_blank": True},
            "ssh_password": {"write_only": True, "required": False, "allow_blank": True},
        }

    def get_ssh_configured(self, obj) -> bool:
        return bool(obj.ssh_key or obj.ssh_password)