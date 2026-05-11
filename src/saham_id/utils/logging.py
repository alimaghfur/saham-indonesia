"""Centralized logging setup using the stdlib `logging`.

Call `configure_logging()` once at application start (the CLI does this).
"""

from __future__ import annotations

import logging

from saham_id.config import settings


def configure_logging(level: str | None = None) -> None:
    lvl = (level or settings.log_level).upper()
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
