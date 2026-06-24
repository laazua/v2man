"""Admin configuration for the nodes app."""

from django.contrib import admin

from .models import Node
from .subscription import Subscription


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    """Admin view for managing V2Ray nodes."""

    list_display = [
        "name",
        "protocol",
        "address",
        "port",
        "is_active",
        "sort_order",
    ]
    list_filter = ["protocol", "is_active"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin view for managing subscriptions."""

    list_display = ["user", "token", "created_at"]
