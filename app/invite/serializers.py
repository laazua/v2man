from rest_framework import serializers
from .models import InviteCode, Referral, Withdrawal, SystemSetting


class InviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteCode
        fields = ['code', 'created_at', 'is_active']


class ReferralSerializer(serializers.ModelSerializer):
    invited_username = serializers.CharField(source='invited.username', read_only=True)
    invited_created = serializers.DateTimeField(source='invited.date_joined', read_only=True)

    class Meta:
        model = Referral
        fields = ['invited_username', 'invited_created', 'earned', 'created_at']


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'amount', 'status', 'created_at', 'processed_at', 'note']
        read_only_fields = ['id', 'status', 'created_at', 'processed_at', 'note']


class AdminWithdrawalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Withdrawal
        fields = ['id', 'username', 'amount', 'status', 'created_at', 'processed_at', 'note']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['key', 'value']
