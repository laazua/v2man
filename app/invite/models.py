"""邀请码、推广关系、提现申请和系统设置模型。"""

import secrets
import string
from typing import Optional

from django.conf import settings
from django.db import models


class InviteCode(models.Model):
    """邀请码模型。"""

    code = models.CharField(max_length=12, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invite_codes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(  # type: ignore[override]
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Optional[str] = None,
        update_fields: Optional[list[str]] = None,
    ) -> None:
        if not self.code:
            alphabet = string.ascii_uppercase + string.digits
            self.code = "".join(secrets.choice(alphabet) for _ in range(8))
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class Referral(models.Model):
    """推荐关系模型。"""

    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals_made",
    )
    invited = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referred_by",
    )
    invite_code = models.ForeignKey(
        InviteCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    earned = models.BigIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.inviter} → {self.invited}"


class Withdrawal(models.Model):
    """提现申请模型。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    STATUS_CHOICES = [
        (PENDING, "待审核"),
        (APPROVED, "已通过"),
        (REJECTED, "已拒绝"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawals",
    )
    amount = models.BigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} ¥{self.amount / 100:.2f} [{self.status}]"


class SystemSetting(models.Model):
    """系统配置键值对模型。"""

    key = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.key}={self.value}"

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        try:
            return int(cls.objects.get(key=key).value)
        except (cls.DoesNotExist, ValueError):
            return default
