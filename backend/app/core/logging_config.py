from __future__ import annotations

import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get("-")
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting utility
        base: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for attr in ("path", "status_code", "method", "latency_ms", "endpoint", "action", "model", "message_count"):
            value = getattr(record, attr, None)
            if value is not None:
                base[attr] = value

        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


def configure_logging(level: str | int = logging.INFO) -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },
        "filters": {"request_id": {"()": RequestIdFilter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["request_id"],
            }
        },
        "root": {"handlers": ["console"], "level": level},
    }
    logging.config.dictConfig(logging_config)
