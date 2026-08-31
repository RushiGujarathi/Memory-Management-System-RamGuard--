"""
RAMGuard Logger Utility
Centralized logging for all RAMGuard modules.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def get_log_directory() -> Path:
    """Get or create the log directory."""
    log_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "RAMGuard") -> logging.Logger:
    """
    Set up and return a configured logger instance.
    
    Args:
        name: Logger name (default: 'RAMGuard')
    
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG and above)
    try:
        log_dir = get_log_directory()
        log_file = log_dir / f"ramguard_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")
    
    return logger


# Module-level logger
logger = setup_logger("RAMGuard")


def get_logger(module_name: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return logging.getLogger(f"RAMGuard.{module_name}")
