from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_pinned', 'is_active', 'created_at']
    list_filter = ['is_pinned', 'is_active']
