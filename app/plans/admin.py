from django.contrib import admin
from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "traffic_limit", "duration_days", "is_active", "sort_order"]
    filter_horizontal = ["nodes"]
