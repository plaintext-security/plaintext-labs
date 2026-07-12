"""Structured logging — logs are data, so emit JSON events with fields.

`log.info("triaged", indicator=..., verdict=...)` is searchable and correlatable;
`print("triaged " + ioc)` is not. This is the telemetry the defensive track consumes.
"""
from __future__ import annotations

import logging

import structlog


def get_logger(level: str = "INFO") -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
    )
    return structlog.get_logger()
