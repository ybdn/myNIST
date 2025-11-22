"""Logging configuration for NIST Studio application."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "NIST Studio", level: int = logging.INFO) -> logging.Logger:
    """
    Set up logger for the application.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"NIST Studio.{name}")
