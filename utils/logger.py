"""Конфигурация structlog (stdlib-интеграция).

Консоль — человекочитаемый вывод, файл — JSON. Оба потока работают
одновременно через стандартный ``logging``.
"""
from __future__ import annotations

import logging
import os
import sys

import structlog

from config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # structlog -> stdlib logging
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Консольный форматтер
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=not settings.debug),
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = []

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(console_formatter)
    root.addHandler(console)

    # Файловый обработчик (JSON)
    if settings.log_file:
        os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
        file_handler.setFormatter(file_formatter)
        root.addHandler(file_handler)


def get_logger(name: str = "couple_bot"):
    return structlog.get_logger(name)
