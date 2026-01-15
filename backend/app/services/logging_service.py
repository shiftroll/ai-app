"""
Logging service for structured logging and request tracking.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log_record.update(record.extra)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging(level: str = "INFO", format: str = "json"):
    """
    Setup application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Log format (json or text)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: Optional[str] = None,
):
    """Log HTTP request"""
    logger = logging.getLogger("http")
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "extra": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }
        },
    )


def log_action(
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: str,
    details: Optional[dict] = None,
):
    """Log business action for audit"""
    logger = logging.getLogger("audit")
    logger.info(
        f"{action} on {entity_type}/{entity_id} by {actor_id}",
        extra={
            "extra": {
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "actor_id": actor_id,
                "details": details,
            }
        },
    )
