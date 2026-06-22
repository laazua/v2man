from django.core.management.base import BaseCommand

from nodes.models import Node
from nodes.ssh_utils import sync_users_to_node


class Command(BaseCommand):
    help = "将所有活跃用户的 UUID 同步到关联的节点"

    def add_arguments(self, parser):
        parser.add_argument("--node", type=str, help="只同步指定节点 (name)")

    def handle(self, *args, **options):
        qs = Node.objects.filter(is_active=True)
        if options["node"]:
            qs = qs.filter(name=options["node"])

        if not qs.exists():
            self.stdout.write("没有活跃节点")
            return

        for node in qs:
            self.stdout.write(f"[{node.name}] 同步用户... ", ending="")
            err = sync_users_to_node(node)
            if err:
                self.stderr.write(self.style.ERROR(f"失败: {err}"))
            else:
                self.stdout.write(self.style.SUCCESS("OK"))
