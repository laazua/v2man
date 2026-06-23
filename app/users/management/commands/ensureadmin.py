"""确保管理员用户存在，若无则自动创建。"""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """确保管理员用户存在，若无则自动创建。"""

    help = (
        'Ensure an admin user exists'
        ' (creates one if none found)'
    )

    def add_arguments(self, parser: Any) -> None:
        """添加命令行参数。"""
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--email', default='admin@v2man.local')

    def handle(self, *args: str, **options: Any) -> None:
        """执行管理员用户创建。"""
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                'Admin user already exists, skipping'
            )
            return

        User.objects.create_superuser(
            username=options['username'],
            password=options['password'],
            email=options['email'],
        )
        self.stdout.write(self.style.SUCCESS(
            f'Admin user [{options["username"]}]'
            ' created successfully'
        ))
