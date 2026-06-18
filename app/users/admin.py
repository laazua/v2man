from django.contrib import admin
from django.utils import timezone
from .models import User
from .wallet import Wallet, Recharge, PaymentConfig
from invite.models import Referral, SystemSetting


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'plan', 'traffic_used', 'traffic_total', 'expire_date', 'is_active']
    list_filter = ['plan', 'is_active']
    search_fields = ['username', 'email']


@admin.register(Recharge)
class RechargeAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'status', 'created_at', 'confirmed_at']
    list_filter = ['status']
    actions = ['confirm_recharge']

    @admin.display(description='金额')
    def amount_display(self, obj):
        return f'¥{obj.amount / 100:.2f}'

    def confirm_recharge(self, request, queryset):
        count = 0
        for r in queryset.filter(status='pending'):
            r.status = 'completed'
            r.confirmed_at = timezone.now()
            r.save()
            wallet, _ = Wallet.objects.get_or_create(user=r.user)
            wallet.balance += r.amount
            wallet.save()

            try:
                ref = Referral.objects.get(invited=r.user)
                pct = int(SystemSetting.get('referral_percentage', '20'))
                credit = r.amount * pct // 100
                if credit > 0:
                    inviter_wallet, _ = Wallet.objects.get_or_create(user=ref.inviter)
                    inviter_wallet.balance += credit
                    inviter_wallet.save()
                    ref.earned += credit
                    ref.save()
            except Referral.DoesNotExist:
                pass

            count += 1
        self.message_user(request, f'已确认 {count} 笔充值')
    confirm_recharge.short_description = '确认选中的充值'


admin.site.register(Wallet)
admin.site.register(PaymentConfig)
