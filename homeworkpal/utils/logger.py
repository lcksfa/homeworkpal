"""
Logger utility for Homework Pal application.
Provides centralized logging configuration.
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from homeworkpal.core.config import settings


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: str = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        log_file: Log file name (relative to logs directory)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Set log level
    log_level = level or settings.LOG_LEVEL.upper()
    logger.setLevel(getattr(logging, log_level))

    # Clear existing handlers
    logger.handlers.clear()

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Define format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = logs_dir / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name
        log_file: Log file name (optional)

    Returns:
        Logger instance
    """
    return setup_logger(name, log_file)


# Predefined loggers for different components
def get_api_logger() -> logging.Logger:
    """Get API logger."""
    return get_logger("homeworkpal.api", "api.log")


def get_frontend_logger() -> logging.Logger:
    """Get frontend logger."""
    return get_logger("homeworkpal.frontend", "frontend.log")


def get_simple_logger() -> logging.Logger:
    """Get simple API logger."""
    return get_logger("homeworkpal.simple", "simple.log")


def get_database_logger() -> logging.Logger:
    """Get database logger."""
    return get_logger("homeworkpal.database", "database.log")


def get_llm_logger() -> logging.Logger:
    """Get LLM logger."""
    return get_logger("homeworkpal.llm", "llm.log")


def get_vision_logger() -> logging.Logger:
    """Get vision logger."""
    return get_logger("homeworkpal.vision", "vision.log")


# Utility function to create timestamped log files
def get_timestamped_log_filename(base_name: str) -> str:
    """
    Generate a timestamped log filename.

    Args:
        base_name: Base name for the log file

    Returns:
        Timestamped filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.log"