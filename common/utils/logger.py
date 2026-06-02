#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Logger utility for pipelines
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

def get_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Create a logger with JSON formatting
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger

def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs):
    """Log with additional context"""
    record = logger.makeRecord(
        logger.name, getattr(logging, level.upper()), 
        '', 0, message, args=(), exc_info=None
    )
    record.extra_fields = kwargs
    logger.handle(record)
