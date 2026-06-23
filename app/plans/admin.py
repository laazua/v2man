"""Django admin configuration for the plans module."""

from django.contrib import admin

from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin interface for managing Plan records."""

    list_display = [
        "name", "price", "traffic_limit",
        "duration_days", "is_active", "sort_order",
    ]
    filter_horizontal = ["nodes"]
