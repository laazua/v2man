import django.db.models.deletion
from django.db import migrations, models


def convert_replies_to_messages(apps, schema_editor):
    ContactMessage = apps.get_model("contact", "ContactMessage")
    for msg in ContactMessage.objects.exclude(reply=""):
        ContactMessage.objects.create(
            parent=msg,
            user=msg.user,
            message=msg.reply,
            is_admin=True,
            status="replied",
            replied_at=msg.replied_at,
            created_at=msg.replied_at or msg.created_at,
        )
        if msg.status == "pending":
            msg.status = "replied"
            msg.replied_at = msg.replied_at or msg.created_at
            msg.save(update_fields=["status", "replied_at"])


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("contact", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactmessage",
            name="is_admin",
            field=models.BooleanField(
                default=False, verbose_name="管理员消息"
            ),
        ),
        migrations.AddField(
            model_name="contactmessage",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="replies",
                to="contact.contactmessage",
                verbose_name="父消息",
            ),
        ),
        migrations.RunPython(
            convert_replies_to_messages, migrations.RunPython.noop
        ),
    ]
