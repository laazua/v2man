"""Node model for V2Ray server configuration."""

from django.db import models

from config.fields import EncryptedCharField


class Node(models.Model):
    """V2Ray server node with connection and SSH deployment settings."""

    PROTOCOL_CHOICES = [
        ("vless", "VLESS"),
        ("vmess", "VMess"),
        ("shadowsocks", "Shadowsocks"),
        ("trojan", "Trojan"),
        ("hysteria2", "Hysteria2"),
    ]

    name = models.CharField(max_length=128, verbose_name="节点名称")
    protocol = models.CharField(
        max_length=32, choices=PROTOCOL_CHOICES, verbose_name="协议",
    )
    address = models.CharField(max_length=256, verbose_name="地址")
    port = models.IntegerField(verbose_name="端口")
    config = models.JSONField(
        default=dict, blank=True, verbose_name="协议配置",
        help_text="各协议的专属配置，如 flow/encryption/obfs 等",
    )
    config_path = models.CharField(
        max_length=512,
        default="/usr/local/etc/v2ray/config.json",
        verbose_name="V2Ray 配置路径",
        help_text="配置文件路径或配置目录路径，如 /etc/v2ray/configs/",
    )
    reload_cmd = models.CharField(
        max_length=256,
        default="systemctl restart v2ray",
        verbose_name="重载命令",
        help_text="重载 V2Ray 的命令，如 systemctl restart v2ray / v2ray -d <目录> 等",
    )
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name="启用",
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True)
    deployed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="最后部署时间",
    )

    ssh_host = models.CharField(
        max_length=256, blank=True, verbose_name="SSH 地址",
    )
    ssh_port = models.IntegerField(default=22, verbose_name="SSH 端口")
    ssh_user = models.CharField(
        max_length=64, default="root", verbose_name="SSH 用户",
    )
    ssh_key = models.TextField(
        blank=True, verbose_name="SSH 私钥",
        help_text="私钥认证，与密码二选一",
    )
    ssh_password = EncryptedCharField(
        max_length=1024, blank=True, verbose_name="SSH 密码",
        help_text="密码认证，与私钥二选一（自动加密存储）",
    )

    class Meta:
        db_table = "nodes"
        verbose_name = "节点"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.name} ({self.protocol})"
