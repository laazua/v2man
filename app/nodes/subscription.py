"""Subscription model for user subscription tokens."""

import uuid

from django.conf import settings
from django.db import models


class Subscription(models.Model):
    """User subscription with unique token for client configuration."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscriptions"
        verbose_name = "订阅"

    def __str__(self) -> str:
        return f"{self.user} - {self.token}"
