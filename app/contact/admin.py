"""联系反馈管理后台。"""

from django.contrib import admin
from django.http import HttpRequest

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """联系反馈管理。"""
    list_display = [
        "subject", "user", "is_admin", "status",
        "created_at", "replied_at",
    ]
    list_filter = ["status", "is_admin", "created_at"]
    search_fields = ["subject", "message", "user__username"]
    readonly_fields = [
        "user", "subject", "message", "is_admin",
        "parent", "created_at", "replied_at",
    ]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
