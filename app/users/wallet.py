from django.db import models
from django.conf import settings


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet'
    )
    balance = models.BigIntegerField(default=0, verbose_name='余额(分)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        verbose_name = '钱包'

    def __str__(self) -> str:
        return f'{self.user} ¥{self.balance / 100:.2f}'


class Recharge(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recharges'
    )
    amount = models.BigIntegerField(verbose_name='金额(分)')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    admin_remark = models.TextField(blank=True, verbose_name='管理员备注')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')

    class Meta:
        db_table = 'recharges'
        verbose_name = '充值记录'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user} ¥{self.amount / 100:.2f} ({self.status})'
