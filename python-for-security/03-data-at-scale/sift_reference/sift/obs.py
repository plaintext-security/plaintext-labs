"""Structured logging — logs are data, so emit JSON events with fields.

`log.info("triaged", signature=..., dest_ip=..., verdict=...)` is searchable and
correlatable; `print("triaged " + sig)` is not. This is exactly the telemetry the
defensive track (Track 02) parses and detects on — you produce one side of that seam.
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


def verdict_for_severity(severity: int) -> str:
    """Map Suricata alert severity (1=highest priority .. 3=informational) to a triage verdict."""
    return {1: "malicious", 2: "suspicious", 3: "informational"}.get(severity, "unknown")
