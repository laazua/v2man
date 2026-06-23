"""Traffic log model definition."""

from django.conf import settings
from django.db import models


class TrafficLog(models.Model):
    """Records upload/download traffic for a user at a point in time."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="traffic_logs",
    )
    upload_bytes = models.BigIntegerField(
        default=0, verbose_name="上传字节"
    )
    download_bytes = models.BigIntegerField(
        default=0, verbose_name="下载字节"
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True, verbose_name="记录时间"
    )
    node_name = models.CharField(
        max_length=128, blank=True, verbose_name="节点名称"
    )

    class Meta:
        db_table = "traffic_logs"
        verbose_name = "流量日志"
        ordering = ["-recorded_at"]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.user} @ {self.recorded_at:%Y-%m-%d}"
