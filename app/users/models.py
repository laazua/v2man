"""User model definition for the v2man application."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with plan, traffic tracking, and expiration."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    plan = models.ForeignKey(
        "plans.Plan", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="当前套餐",
    )
    traffic_used = models.BigIntegerField(
        default=0, verbose_name="已用流量(MB)",
    )
    traffic_total = models.BigIntegerField(
        default=0, verbose_name="总流量(MB)",
    )
    expire_date = models.DateTimeField(
        null=True, blank=True, db_index=True, verbose_name="到期时间",
    )

    class Meta:
        db_table = "users"
        verbose_name = "用户"

    def __str__(self) -> str:
        """Return the username as string representation."""
        return self.username
