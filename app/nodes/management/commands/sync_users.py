"""将所有活跃用户的 UUID 同步到关联的节点。"""

import logging
from typing import Any

from django.core.management.base import BaseCommand

from nodes.models import Node
from nodes.ssh_utils import sync_users_to_node

logger = logging.getLogger("business")


class Command(BaseCommand):
    """将所有活跃用户的 UUID 同步到关联的节点。"""

    help = "将所有活跃用户的 UUID 同步到关联的节点"

    def add_arguments(self, parser: Any) -> None:
        """添加命令行参数。"""
        parser.add_argument(
            "--node",
            type=str,
            help="只同步指定节点 (name)",
        )

    def handle(self, *args: str, **options: Any) -> None:
        """执行用户同步。"""
        qs = Node.objects.filter(is_active=True)
        if options["node"]:
            qs = qs.filter(name=options["node"])

        if not qs.exists():
            self.stdout.write("没有活跃节点")
            return

        ok = 0
        fail = 0
        for node in qs:
            self.stdout.write(f"[{node.name}] 同步用户... ", ending="")
            err = sync_users_to_node(node)
            if err:
                self.stderr.write(self.style.ERROR(f"失败: {err}"))
                fail += 1
            else:
                self.stdout.write(self.style.SUCCESS("OK"))
                ok += 1
        logger.info("定时同步用户完成: 成功=%s 失败=%s", ok, fail)
