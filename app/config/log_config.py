"""
Custom logging handlers and utilities for v2man project.
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class SizeAndTimeRotatingFileHandler(TimedRotatingFileHandler):
    """
    同时按天和文件大小切割的日志处理器

    每天一个日志文件，文件超过 max_bytes 时也切割。
    """

    def __init__(  # noqa: PLR0913
        self,
        filename: str,
        when: str = 'midnight',
        interval: int = 1,
        backup_count: int = 30,
        max_bytes: int = 100 * 1024 * 1024,
        encoding: str = 'utf-8',
        delay: bool = False,
        utc: bool = False,
        at_time=None,
    ) -> None:
        """Initialize handler with both time and size rotation."""
        self.max_bytes = max_bytes
        super().__init__(
            filename, when=when, interval=interval,
            backupCount=backup_count, encoding=encoding,
            delay=delay, utc=utc, atTime=at_time,
        )

    def _open(self) -> logging.StreamHandler:
        """Ensure log directory exists before opening."""
        os.makedirs(os.path.dirname(self.baseFilename), exist_ok=True)
        return super()._open()

    def should_rollover(
        self, record: logging.LogRecord
    ) -> bool:  # type: ignore[override]
        """Roll over on time interval or when file exceeds max_bytes."""
        if super().should_rollover(record):
            return True
        if self.stream is None:
            return False
        try:
            cur_size = self.stream.tell()
            return cur_size >= self.max_bytes
        except OSError:
            return False


_LOG_DIR: Path = Path(__file__).resolve().parent.parent / 'logs'


def ensure_log_dir() -> None:
    """Create the log directory if it does not exist."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_path(name: str) -> str:
    """Return the full path for a log file with the given name."""
    return str(_LOG_DIR / f'{name}.log')


def setup_logging() -> tuple[logging.Handler, logging.Handler]:
    """Configure and return API and business log handlers."""
    ensure_log_dir()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    api_handler = SizeAndTimeRotatingFileHandler(
        filename=get_log_path('api-requests'),
        when='midnight',
        interval=1,
        backup_count=30,
        max_bytes=100 * 1024 * 1024,
    )
    api_handler.setFormatter(formatter)
    api_handler.setLevel(logging.INFO)

    biz_handler = SizeAndTimeRotatingFileHandler(
        filename=get_log_path('business'),
        when='midnight',
        interval=1,
        backup_count=30,
        max_bytes=100 * 1024 * 1024,
    )
    biz_handler.setFormatter(formatter)
    biz_handler.setLevel(logging.INFO)

    error_handler = SizeAndTimeRotatingFileHandler(
        filename=get_log_path('error'),
        when='midnight',
        interval=1,
        backup_count=90,
        max_bytes=100 * 1024 * 1024,
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.WARNING)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)

    return api_handler, biz_handler
