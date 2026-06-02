#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time and date utilities
"""

from datetime import datetime, timedelta
import pandas as pd
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class TimeUtils:
    """Time and date utilities"""
    
    @staticmethod
    def get_business_days(start_date: str, end_date: str) -> List[str]:
        """Get list of business days between dates"""
        try:
            date_range = pd.bdate_range(start=start_date, end=end_date)
            return date_range.strftime('%Y-%m-%d').tolist()
        except Exception as e:
            logger.error(f"Error getting business days: {e}")
            raise
    
    @staticmethod
    def get_date_range(start_date: str, end_date: str) -> List[str]:
        """Get list of dates between range"""
        try:
            date_range = pd.date_range(start=start_date, end=end_date)
            return date_range.strftime('%Y-%m-%d').tolist()
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            raise
    
    @staticmethod
    def get_month_range(start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """Get month ranges between two dates"""
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            months = []
            
            current = start
            while current <= end:
                month_start = current.replace(day=1)
                month_end = (current + pd.offsets.MonthEnd(0)).replace(day=31)
                
                if month_end > end:
                    month_end = end
                
                months.append((
                    month_start.strftime('%Y-%m-%d'),
                    month_end.strftime('%Y-%m-%d')
                ))
                
                current = month_end + timedelta(days=1)
            
            return months
        except Exception as e:
            logger.error(f"Error getting month range: {e}")
            raise
    
    @staticmethod
    def get_fiscal_year(date: str) -> int:
        """Get fiscal year from date (assuming Jan 1st - Dec 31st)"""
        try:
            dt = pd.to_datetime(date)
            return dt.year
        except Exception as e:
            logger.error(f"Error getting fiscal year: {e}")
            raise
