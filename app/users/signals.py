"""Signal handlers for automatic resource creation on user registration."""

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from nodes.subscription import Subscription

from .wallet import Wallet

logger = logging.getLogger("business")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet_and_subscription(
    sender,
    instance,
    created,
    **kwargs,
) -> None:
    """Create a wallet and subscription when a new user is registered."""
    if created:
        wallet = Wallet.objects.create(user=instance)
        sub = Subscription.objects.create(user=instance)
        logger.info(
            "用户注册信号: user_id=%s wallet_id=%s subscription_token=%s",
            instance.id,
            wallet.id,
            sub.token,
        )
