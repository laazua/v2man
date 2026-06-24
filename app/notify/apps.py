"""通知 App 配置。"""

from django.apps import AppConfig


class NotifyConfig(AppConfig):
    """通知应用配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notify"
