from django.db import migrations


def encrypt_existing_passwords(apps, schema_editor):
    Node = apps.get_model("nodes", "Node")
    for node in Node.objects.all():
        if node.ssh_password:
            node.save(update_fields=["ssh_password"])


class Migration(migrations.Migration):
    dependencies = [
        ("nodes", "0009_alter_node_ssh_password"),
    ]

    operations = [
        migrations.RunPython(
            encrypt_existing_passwords, migrations.RunPython.noop
        ),
    ]
