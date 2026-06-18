from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .wallet import Wallet
from nodes.subscription import Subscription


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet_and_subscription(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        Subscription.objects.create(user=instance)
