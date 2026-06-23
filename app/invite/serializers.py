"""邀请码、推广、提现序列化器。"""

from rest_framework import serializers

from .models import InviteCode, Referral, Withdrawal, SystemSetting


class InviteCodeSerializer(serializers.ModelSerializer):
    """邀请码序列化器。"""

    class Meta:
        model = InviteCode
        fields = ['code', 'created_at', 'is_active']


class ReferralSerializer(serializers.ModelSerializer):
    """推广记录序列化器。"""
    invited_username = serializers.CharField(
        source='invited.username', read_only=True,
    )
    invited_created = serializers.DateTimeField(
        source='invited.date_joined', read_only=True,
    )

    class Meta:
        model = Referral
        fields = [
            'invited_username', 'invited_created',
            'earned', 'created_at',
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    """提现记录序列化器（用户视角）。"""

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'amount', 'status', 'created_at',
            'processed_at', 'note',
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'processed_at', 'note',
        ]


class AdminWithdrawalSerializer(serializers.ModelSerializer):
    """提现记录序列化器（管理员视角）。"""
    username = serializers.CharField(
        source='user.username', read_only=True,
    )

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'username', 'amount', 'status',
            'created_at', 'processed_at', 'note',
        ]


class SystemSettingSerializer(serializers.ModelSerializer):
    """系统设置序列化器。"""

    class Meta:
        model = SystemSetting
        fields = ['key', 'value']
