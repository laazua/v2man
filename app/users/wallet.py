import uuid
import logging
from django.db import models
from django.conf import settings

logger = logging.getLogger('business')


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

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            try:
                old = type(self).objects.get(pk=self.pk)
                if old.balance != self.balance:
                    diff = self.balance - old.balance
                    logger.info('钱包余额变更: user_id=%s 变动=%s 原余额=%s 新余额=%s',
                                self.user_id, diff, old.balance, self.balance)
            except type(self).DoesNotExist:
                pass
        else:
            logger.info('钱包创建: user_id=%s 初始余额=%s', self.user_id, self.balance)
        super().save(*args, **kwargs)


class PaymentConfig(models.Model):
    qr_code = models.ImageField(upload_to='payment/', verbose_name='支付宝收款码')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_config'
        verbose_name = '支付配置'

    def __str__(self) -> str:
        return f'收款码 (更新于 {self.updated_at})'


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
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True, verbose_name='状态')
    admin_remark = models.TextField(blank=True, verbose_name='管理员备注')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')

    class Meta:
        db_table = 'recharges'
        verbose_name = '充值记录'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user} ¥{self.amount / 100:.2f} ({self.status})'


class PaymentOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('closed', '已关闭'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_orders'
    )
    amount = models.BigIntegerField(verbose_name='金额(分)')
    out_trade_no = models.CharField(max_length=64, unique=True, verbose_name='商户订单号')
    trade_no = models.CharField(max_length=64, blank=True, default='', verbose_name='支付宝交易号')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')

    class Meta:
        db_table = 'payment_orders'
        verbose_name = '支付订单'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.out_trade_no} ¥{self.amount / 100:.2f} ({self.status})'
