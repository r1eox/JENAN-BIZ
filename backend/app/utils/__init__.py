"""
Logger utility — Loguru configuration.
"""

import sys
from loguru import logger

from app.config import get_settings

settings = get_settings()


def setup_logger():
    """Configure Loguru for structured logging."""
    logger.remove()  # Remove default handler

    # Console
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File (JSON for production)
    logger.add(
        "logs/jenanbiz_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8",
    )
