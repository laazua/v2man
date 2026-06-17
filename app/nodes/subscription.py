import uuid
import base64
import json

from django.db import models
from django.conf import settings


class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscriptions"
        verbose_name = "订阅"

    def __str__(self) -> str:
        return f"{self.user} - {self.token}"
