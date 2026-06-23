"""从所有活跃节点采集流量数据并写入数据库。"""

import math
import logging
from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Sum

from nodes.models import Node
from nodes.ssh_utils import collect_node_traffic
from traffic.models import TrafficLog

logger = logging.getLogger('business')
User = get_user_model()


class Command(BaseCommand):
    """采集所有活跃节点上 v2ray 用户的流量数据。"""

    help = "从所有活跃节点采集流量数据并写入数据库"

    def add_arguments(self, parser: Any) -> None:
        """添加命令行参数。"""
        parser.add_argument("--node", type=str, help="只采集指定节点 (name)")

    def handle(self, *args: str, **options: Any) -> None:
        """执行流量采集。"""
        qs = Node.objects.filter(is_active=True)
        if options["node"]:
            qs = qs.filter(name=options["node"])

        if not qs.exists():
            self.stdout.write("没有活跃节点")
            return

        now = datetime.now()
        total_mb = 0
        total_records = 0

        for node in qs:
            self.stdout.write(f"[{node.name}] 采集... ", ending="")
            result = collect_node_traffic(node)
            if "error" in result:
                self.stderr.write(self.style.ERROR(
                    f"失败: {result['error']}"
                ))
                continue

            if not result:
                self.stdout.write(self.style.WARNING("无流量数据"))
                continue

            count = 0
            for email_prefix, counters in result.items():
                try:
                    user = User.objects.get(username=email_prefix)
                except User.DoesNotExist:
                    self.stdout.write(
                        f"  跳过未知用户: {email_prefix}"
                    )
                    continue

                uplink = counters["uplink"]
                downlink = counters["downlink"]
                total_bytes = uplink + downlink
                if total_bytes <= 0:
                    continue

                midnight = now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                recent = TrafficLog.objects.filter(
                    user=user,
                    node_name=node.name,
                    recorded_at__gte=midnight,
                ).aggregate(
                    u=Sum('upload_bytes'), d=Sum('download_bytes')
                )
                if (
                    (recent['u'] or 0) >= uplink
                    and (recent['d'] or 0) >= downlink
                ):
                    self.stdout.write(
                        f"  跳过 {user.username}"
                        "（当日已有相同或更大流量记录）"
                    )
                    continue

                TrafficLog.objects.create(
                    user=user,
                    upload_bytes=uplink,
                    download_bytes=downlink,
                    node_name=node.name,
                    recorded_at=now,
                )

                mb = max(1, math.ceil(total_bytes / (1024 * 1024)))
                user.traffic_used = (user.traffic_used or 0) + mb
                user.save(update_fields=["traffic_used"])

                if (
                    user.traffic_total > 0
                    and user.traffic_used >= user.traffic_total
                ):
                    msg = (
                        f"  {user.username} 流量已用完 "
                        f"({user.traffic_used}/{user.traffic_total} MB)"
                    )
                    self.stdout.write(self.style.WARNING(msg))

                total_mb += mb
                total_records += 1
                count += 1

            self.stdout.write(self.style.SUCCESS(
                f"OK ({count} 用户, {count} 条记录)"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\n完成: {total_records} 条记录, {total_mb} MB"
        ))
        logger.info(
            '定时采集流量完成: 节点数=%s 记录数=%s 流量=%sMB',
            qs.count(), total_records, total_mb,
        )
