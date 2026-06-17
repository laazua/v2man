from django.contrib import admin
from .models import TrafficLog


@admin.register(TrafficLog)
class TrafficLogAdmin(admin.ModelAdmin):
    list_display = ["user", "upload_bytes", "download_bytes", "recorded_at", "node_name"]
    list_filter = ["recorded_at"]
    date_hierarchy = "recorded_at"
