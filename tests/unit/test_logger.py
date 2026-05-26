#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for logger utility
"""

import pytest
from pipelines.utils.logger import get_logger, JSONFormatter
import logging

def test_get_logger():
    """Test logger creation"""
    logger = get_logger('test_logger', level='INFO')
    assert logger is not None
    assert logger.name == 'test_logger'
    assert logger.level == logging.INFO

def test_logger_output(caplog):
    """Test logger output"""
    logger = get_logger('test_output')
    logger.info("Test message")
    assert "Test message" in caplog.text

def test_json_formatter():
    """Test JSON formatting"""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='test.py',
        lineno=1,
        msg='Test message',
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert 'timestamp' in formatted
    assert 'level' in formatted
    assert 'Test message' in formatted
