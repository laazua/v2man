"""用户联系反馈消息模型。"""

from django.conf import settings
from django.db import models


class ContactMessage(models.Model):
    """用户联系反馈消息模型，支持工单式回复。"""
    STATUS_CHOICES = [
        ("pending", "待回复"),
        ("replied", "已回复"),
    ]

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE,
        related_name="replies", verbose_name="父消息",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_messages",
        verbose_name="用户",
    )
    subject = models.CharField(
        max_length=200, blank=True, verbose_name="主题",
    )
    message = models.TextField(verbose_name="内容")
    is_admin = models.BooleanField(default=False, verbose_name="管理员消息")
    visible_to_user = models.BooleanField(
        default=True, verbose_name="用户可见",
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending",
        db_index=True, verbose_name="状态",
    )
    replied_at = models.DateTimeField(
        null=True, blank=True, verbose_name="最后回复时间",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="提交时间",
    )

    class Meta:
        db_table = "contact_messages"
        verbose_name = "联系记录"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.parent_id:
            prefix = "[回复] "
        else:
            prefix = f"[{self.get_status_display()}] "
        return f"{prefix}{self.subject or '(无主题)'}"
