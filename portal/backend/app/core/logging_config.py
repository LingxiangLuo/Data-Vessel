"""结构化日志配置：JSON 格式输出 + request_id 注入。"""

import json
import logging
import sys
from typing import Any

from app.core.request_id import get_request_id


class RequestIdFilter(logging.Filter):
    """将当前上下文的 request_id 注入 LogRecord。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"  # type: ignore[attr-defined]
        return True


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式器。"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        # 异常信息
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        # 额外字段
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
                "request_id",
            }:
                log_obj[key] = value
        return json.dumps(log_obj, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """开发环境彩色文本格式器（保留人类可读性）。"""

    COLORS = {
        "DEBUG": "\033[36m",      # cyan
        "INFO": "\033[32m",       # green
        "WARNING": "\033[33m",    # yellow
        "ERROR": "\033[31m",      # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""
        req_id = getattr(record, "request_id", "-")
        return (
            f"{self.formatTime(record)} | {color}{record.levelname:<8}{reset} | "
            f"{record.name} | [{req_id}] {record.getMessage()}"
        )


def setup_logging(json_format: bool = False) -> None:
    """配置根日志记录器。

    Args:
        json_format: True 输出 JSON（生产环境），False 输出彩色文本（开发环境）
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ColoredFormatter())

    root = logging.getLogger()
    root.handlers = []  # 清除已有 handler，避免重复
    root.addHandler(handler)
    root.setLevel(logging.INFO)
