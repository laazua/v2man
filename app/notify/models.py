"""通知与已读记录模型。"""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """系统通知模型。"""

    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False, verbose_name="置顶")
    is_active = models.BooleanField(default=True, verbose_name="显示")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        verbose_name = "通知"
        verbose_name_plural = "通知"

    def __str__(self) -> str:
        return self.title


class NotificationRead(models.Model):
    """通知已读记录模型。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_reads",
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="reads",
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "notification"]
        verbose_name = "已读记录"
        verbose_name_plural = "已读记录"

    def __str__(self) -> str:
        return f"{self.user} 已读 {self.notification}"
