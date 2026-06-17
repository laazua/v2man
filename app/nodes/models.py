from django.db import models


class Node(models.Model):
    PROTOCOL_CHOICES = [
        ("vless", "VLESS"),
        ("vmess", "VMess"),
        ("shadowsocks", "Shadowsocks"),
        ("trojan", "Trojan"),
        ("hysteria2", "Hysteria2"),
    ]

    name = models.CharField(max_length=128, verbose_name="节点名称")
    protocol = models.CharField(max_length=32, choices=PROTOCOL_CHOICES, verbose_name="协议")
    address = models.CharField(max_length=256, verbose_name="地址")
    port = models.IntegerField(verbose_name="端口")
    config = models.JSONField(default=dict, blank=True, verbose_name="协议配置",
                              help_text="各协议的专属配置，如 flow/encryption/obfs 等")
    is_active = models.BooleanField(default=True, verbose_name="启用")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "nodes"
        verbose_name = "节点"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.protocol})"
