from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Ensure an admin user exists (creates one if none found)'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--password', default='admin123')
        parser.add_argument('--email', default='admin@v2man.local')

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Admin user already exists, skipping')
            return

        User.objects.create_superuser(
            username=options['username'],
            password=options['password'],
            email=options['email'],
        )
        self.stdout.write(self.style.SUCCESS(
            f'Admin user [{options["username"]}] created successfully'
        ))
