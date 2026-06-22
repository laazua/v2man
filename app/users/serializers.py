from rest_framework import serializers
from .models import User
from .wallet import Recharge, PaymentOrder


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    invite_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'invite_code']

    def create(self, validated_data):
        validated_data.pop('invite_code', None)
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True, default=None)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'uuid', 'plan_name', 'balance',
                  'traffic_used', 'traffic_total', 'expire_date', 'date_joined', 'is_staff']

    def get_balance(self, obj):
        try:
            return obj.wallet.balance
        except Exception:
            return 0


class RechargeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Recharge
        fields = ['id', 'user', 'username', 'amount', 'status', 'admin_remark', 'created_at', 'confirmed_at']


class PaymentOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentOrder
        fields = ['id', 'amount', 'out_trade_no', 'trade_no', 'status', 'created_at', 'paid_at']
        read_only_fields = ['id', 'out_trade_no', 'trade_no', 'status', 'created_at', 'paid_at']
