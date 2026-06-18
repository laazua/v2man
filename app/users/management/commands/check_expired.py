from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = '检查到期用户，重置流量并清除套餐'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = User.objects.filter(
            expire_date__isnull=False, expire_date__lte=now
        ).exclude(plan__isnull=True)
        count = expired.count()
        expired.update(
            traffic_used=0,
            traffic_total=0,
            plan=None,
        )
        self.stdout.write(self.style.SUCCESS(f'已重置 {count} 个到期用户的流量和套餐'))
