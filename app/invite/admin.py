from django.contrib import admin
from .models import InviteCode, Referral, Withdrawal, SystemSetting


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'owner', 'created_at', 'is_active']
    list_filter = ['is_active']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['inviter', 'invited', 'earned', 'created_at']


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at', 'processed_at']
    list_filter = ['status']
    actions = ['approve_withdrawals', 'reject_withdrawals']

    def approve_withdrawals(self, request, queryset):
        from django.utils import timezone
        from django.db import transaction
        count = 0
        for w in queryset.filter(status=Withdrawal.PENDING):
            with transaction.atomic():
                w = Withdrawal.objects.select_for_update().get(id=w.id)
                if w.status != Withdrawal.PENDING:
                    continue
                w.status = Withdrawal.APPROVED
                w.processed_at = timezone.now()
                w.save()
                count += 1
        self.message_user(request, f'已通过 {count} 个提现申请')
    approve_withdrawals.short_description = '通过选中的提现申请'

    def reject_withdrawals(self, request, queryset):
        from django.utils import timezone
        from django.db import transaction
        from users.wallet import Wallet
        count = 0
        for w in queryset.filter(status=Withdrawal.PENDING):
            with transaction.atomic():
                w = Withdrawal.objects.select_for_update().get(id=w.id)
                if w.status != Withdrawal.PENDING:
                    continue
                w.status = Withdrawal.REJECTED
                w.processed_at = timezone.now()
                wallet = Wallet.objects.get(user=w.user)
                wallet.balance += w.amount
                wallet.save()
                w.save()
                count += 1
        self.message_user(request, f'已拒绝并退回 {count} 笔金额')
    reject_withdrawals.short_description = '拒绝并退回金额'


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
