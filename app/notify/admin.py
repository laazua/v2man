"""通知管理后台。"""

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """通知管理。"""
    list_display = ['title', 'is_pinned', 'is_active', 'created_at']
    list_filter = ['is_pinned', 'is_active']
