from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Adjunta un StreamHandler JSON al logger 'agent' sin tocar el root.

    Idempotente: si ya hay un StreamHandler con JsonFormatter, no añade otro.
    """
    agent_logger = logging.getLogger("agent")
    already = any(
        isinstance(h, logging.StreamHandler) and isinstance(h.formatter, JsonFormatter)
        for h in agent_logger.handlers
    )
    if not already:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        agent_logger.addHandler(handler)
    agent_logger.setLevel(level)
    agent_logger.propagate = False
