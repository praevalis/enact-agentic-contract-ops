"""Shared application logging configuration."""

import logging

from enact.platform.middleware.request_context import request_id_context


class RequestContextFilter(logging.Filter):
    """Add the current request ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach the request context to a log record.

        Args:
            record: Log record being processed by a configured handler.

        Returns:
            Whether the record should be emitted.
        """
        record.request_id = request_id_context.get()
        return True


def configure_logging(log_level: str) -> None:
    """Configure application logging.

    Args:
        log_level: The root log level to apply.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s %(levelname)s [%(name)s] [request_id=%(request_id)s] %(message)s',
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestContextFilter())
    logging.captureWarnings(True)
