"""检查到期用户，重置流量并清除套餐。"""

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User

logger = logging.getLogger('business')


class Command(BaseCommand):
    """检查到期用户，重置流量并清除套餐。"""

    help = '检查到期用户，重置流量并清除套餐'

    def handle(self, *args: str, **options: Any) -> None:
        """执行到期用户检查与重置。"""
        now = timezone.now()
        expired = User.objects.filter(
            expire_date__isnull=False, expire_date__lte=now
        ).exclude(plan__isnull=True)
        count = expired.count()
        expired.update(
            traffic_used=0,
            traffic_total=0,
            plan=None,
            is_active=False,
        )
        self.stdout.write(self.style.SUCCESS(
            f'已重置 {count} 个到期用户的流量和套餐'
        ))
        if count > 0:
            logger.info('定时检查到期: 已重置 %s 个用户', count)
