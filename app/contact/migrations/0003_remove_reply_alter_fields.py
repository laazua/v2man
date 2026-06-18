from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_contactmessage_parent_is_admin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contactmessage',
            name='reply',
        ),
        migrations.AlterField(
            model_name='contactmessage',
            name='replied_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最后回复时间'),
        ),
        migrations.AlterField(
            model_name='contactmessage',
            name='subject',
            field=models.CharField(blank=True, max_length=200, verbose_name='主题'),
        ),
    ]
