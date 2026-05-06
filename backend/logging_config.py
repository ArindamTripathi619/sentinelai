"""
Structured logging configuration for SentinelAI.
Provides JSON-formatted logs for centralized log aggregation.
"""

import logging
import json
import sys
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger


class SentinelAIFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds context to log records."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add module name for tracing
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process ID
        log_record['pid'] = os.getpid()


def setup_logging(log_level: str = "INFO"):
    """
    Configure structured JSON logging for SentinelAI.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    log_level = os.getenv("LOG_LEVEL", log_level).upper()
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # JSON console handler (for centralized log aggregation)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Use custom JSON formatter
    formatter = SentinelAIFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # Suppress overly verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a structured logger instance."""
    return logging.getLogger(name)
