"""邀请码 App 配置。"""

from django.apps import AppConfig


class InviteConfig(AppConfig):
    """邀请码应用配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "invite"
