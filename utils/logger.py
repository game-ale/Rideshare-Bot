"""
Logging configuration for the Rideshare Bot.
Provides structured logging with correlation IDs for production-level debugging.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from config import LOG_LEVEL

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class CorrelationFilter(logging.Filter):
    """
    Adds correlation ID (ride_id) to log records for better tracing.
    This makes debugging production issues much easier.
    """
    def filter(self, record):
        if not hasattr(record, 'ride_id'):
            record.ride_id = '-'
        if not hasattr(record, 'user_id'):
            record.user_id = '-'
        return True


def setup_logger(name: str = "rideshare_bot") -> logging.Logger:
    """
    Configure and return a logger with both file and console handlers.
    
    Log format: [2026-02-04 10:47:28] [INFO] [ride_id=42] [user_id=123] Message
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Add correlation filter
    correlation_filter = CorrelationFilter()
    
    # Format with correlation IDs
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [ride_id=%(ride_id)s] [user_id=%(user_id)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    logger.addHandler(console_handler)
    
    # File handler (all logs)
    file_handler = logging.FileHandler(LOGS_DIR / "rideshare_bot.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)
    logger.addHandler(file_handler)
    
    # Error file handler (errors only)
    error_handler = logging.FileHandler(LOGS_DIR / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(correlation_filter)
    logger.addHandler(error_handler)
    
    return logger


def log_with_context(logger: logging.Logger, level: str, message: str, 
                     ride_id: Optional[int] = None, user_id: Optional[int] = None):
    """
    Log a message with correlation context.
    
    Example:
        log_with_context(logger, "INFO", "Driver accepted ride", ride_id=42, user_id=123)
        Output: [INFO] [ride_id=42] [user_id=123] Driver accepted ride
    """
    extra = {
        'ride_id': ride_id or '-',
        'user_id': user_id or '-'
    }
    getattr(logger, level.lower())(message, extra=extra)


# Create default logger instance
logger = setup_logger()
