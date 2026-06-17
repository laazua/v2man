from rest_framework import serializers
from .models import User
from .wallet import Recharge


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True, default=None)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'uuid', 'plan_name', 'balance',
                  'traffic_used', 'traffic_total', 'expire_date', 'date_joined', 'is_staff']

    def get_balance(self, obj):
        wallet = getattr(obj, 'wallet', None)
        return wallet.balance if wallet else 0


class RechargeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Recharge
        fields = ['id', 'user', 'username', 'amount', 'status', 'admin_remark', 'created_at', 'confirmed_at']
