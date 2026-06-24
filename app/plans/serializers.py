"""Serializers for the plans module."""

from rest_framework import serializers

from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    """Plan model serializer with a formatted price display."""

    price_display = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = "__all__"

    def get_price_display(self, obj: Plan) -> str:
        """Return price formatted with yen symbol."""
        return f"¥{obj.price}"
