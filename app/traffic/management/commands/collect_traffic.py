import math
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from nodes.models import Node
from nodes.ssh_utils import collect_node_traffic
from traffic.models import TrafficLog

User = get_user_model()


class Command(BaseCommand):
    help = "从所有活跃节点采集流量数据并写入数据库"

    def add_arguments(self, parser):
        parser.add_argument("--node", type=str, help="只采集指定节点 (name)")

    def handle(self, *args, **options):
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
                self.stderr.write(self.style.ERROR(f"失败: {result['error']}"))
                continue

            if not result:
                self.stdout.write(self.style.WARNING("无流量数据"))
                continue

            count = 0
            for email_prefix, counters in result.items():
                try:
                    user = User.objects.get(username=email_prefix)
                except User.DoesNotExist:
                    self.stdout.write(f"  跳过未知用户: {email_prefix}")
                    continue

                uplink = counters["uplink"]
                downlink = counters["downlink"]
                total_bytes = uplink + downlink
                if total_bytes <= 0:
                    continue

                from django.db.models import Sum
                recent = TrafficLog.objects.filter(
                    user=user, node_name=node.name,
                    recorded_at__gte=now.replace(hour=0, minute=0, second=0, microsecond=0),
                ).aggregate(u=Sum('upload_bytes'), d=Sum('download_bytes'))
                if (recent['u'] or 0) >= uplink and (recent['d'] or 0) >= downlink:
                    self.stdout.write(f"  跳过 {user.username}（当日已有相同或更大流量记录）")
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

                if user.traffic_total > 0 and user.traffic_used >= user.traffic_total:
                    self.stdout.write(self.style.WARNING(
                        f"  {user.username} 流量已用完 ({user.traffic_used}/{user.traffic_total} MB)"
                    ))

                total_mb += mb
                total_records += 1
                count += 1

            self.stdout.write(self.style.SUCCESS(f"OK ({count} 用户, {count} 条记录)"))

        self.stdout.write(self.style.SUCCESS(
            f"\n完成: {total_records} 条记录, {total_mb} MB"
        ))
