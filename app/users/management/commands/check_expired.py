from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = '检查到期用户并自动停用'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = User.objects.filter(
            is_active=True, expire_date__isnull=False, expire_date__lte=now
        )
        count = expired.count()
        expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'已停用 {count} 个到期用户'))
