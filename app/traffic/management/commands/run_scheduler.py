"""启动后台调度器，定时执行管理命令。"""

import logging
import signal
import sys
import time
from typing import Any

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger('scheduler')


class Command(BaseCommand):
    """启动后台调度器，定时执行管理命令。"""

    help = (
        "启动后台调度器，定时执行"
        " collect_traffic / sync_users / check_expired"
    )

    def handle(self, *args: str, **options: Any) -> None:
        """启动调度器并阻塞等待信号。"""
        scheduler = BackgroundScheduler(daemon=False)

        scheduler.add_job(
            lambda: call_command('collect_traffic'),
            IntervalTrigger(minutes=5),
            id='collect_traffic',
            name='采集节点流量',
            replace_existing=True,
        )

        scheduler.add_job(
            lambda: call_command('sync_users'),
            IntervalTrigger(minutes=15),
            id='sync_users',
            name='同步用户到节点',
            replace_existing=True,
        )

        scheduler.add_job(
            lambda: call_command('check_expired'),
            IntervalTrigger(hours=6),
            id='check_expired',
            name='检查到期用户',
            replace_existing=True,
        )

        def job_listener(event: Any) -> None:
            """监听任务执行结果。"""
            if event.exception:
                logger.error(
                    f'[{event.job_id}] 执行失败: {event.exception}'
                )
            else:
                logger.info(f'[{event.job_id}] 执行成功')

        scheduler.add_listener(
            job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        scheduler.start()
        self.stdout.write(self.style.SUCCESS(
            '调度器已启动: collect_traffic(5min),'
            ' sync_users(15min), check_expired(6h)'
        ))

        def shutdown(signum: Any, frame: Any) -> None:
            """关闭调度器并退出。"""
            self.stdout.write('正在关闭调度器...')
            scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            shutdown(None, None)
