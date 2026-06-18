from rest_framework import serializers
from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = '__all__'

    def get_price_display(self, obj):
        return f'¥{obj.price}'
