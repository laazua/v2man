"""Plan model definition."""

from django.db import models


class Plan(models.Model):
    """A purchasable plan with traffic and duration limits."""

    name = models.CharField(max_length=64, verbose_name="套餐名称")
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="价格"
    )
    traffic_limit = models.BigIntegerField(
        verbose_name="流量上限(MB)", help_text="单位 MB，0 表示不限"
    )
    duration_days = models.IntegerField(verbose_name="有效期(天)")
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name="启用"
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    nodes = models.ManyToManyField(
        "nodes.Node", blank=True, verbose_name="关联节点"
    )

    class Meta:
        db_table = "plans"
        verbose_name = "套餐"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{self.name} ¥{self.price}"
