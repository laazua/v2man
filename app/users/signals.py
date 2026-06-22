import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .wallet import Wallet
from nodes.subscription import Subscription

logger = logging.getLogger('business')


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet_and_subscription(sender, instance, created, **kwargs):
    if created:
        wallet = Wallet.objects.create(user=instance)
        sub = Subscription.objects.create(user=instance)
        logger.info('用户注册信号: user_id=%s wallet_id=%s subscription_token=%s',
                    instance.id, wallet.id, sub.token)
