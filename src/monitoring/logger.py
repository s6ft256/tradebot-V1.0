"""
Logging configuration for the trading bot.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file with timestamp
LOG_FILE = LOGS_DIR / f"bot_{datetime.utcnow().strftime('%Y%m%d')}.log"

# Configure logging format
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Root logger
    logging.basicConfig(
        level=log_level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            # Console output
            logging.StreamHandler(sys.stdout),
            # File output
            logging.FileHandler(LOG_FILE),
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
