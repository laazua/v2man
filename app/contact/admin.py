from django.contrib import admin
from django.utils import timezone

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "user", "is_admin", "status", "created_at", "replied_at"]
    list_filter = ["status", "is_admin", "created_at"]
    search_fields = ["subject", "message", "user__username"]
    readonly_fields = ["user", "subject", "message", "is_admin", "parent", "created_at", "replied_at"]

    def has_add_permission(self, request):
        return False
