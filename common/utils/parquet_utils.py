#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parquet utilities for data I/O operations
"""

import pyarrow.parquet as pq
from pyarrow import Table
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ParquetHandler:
    """Utilities for Parquet file operations"""
    
    @staticmethod
    def read_parquet(path: str, columns: Optional[list] = None) -> pd.DataFrame:
        """Read Parquet file into DataFrame"""
        try:
            df = pd.read_parquet(path, columns=columns)
            logger.info(f"Read parquet file: {path} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Error reading parquet: {e}")
            raise
    
    @staticmethod
    def write_parquet(df: pd.DataFrame, path: str, compression: str = 'snappy'):
        """Write DataFrame to Parquet"""
        try:
            df.to_parquet(path, compression=compression, index=False)
            logger.info(f"Wrote parquet file: {path} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"Error writing parquet: {e}")
            raise
    
    @staticmethod
    def get_schema(path: str):
        """Get schema of Parquet file"""
        try:
            parquet_file = pq.ParquetFile(path)
            return parquet_file.schema
        except Exception as e:
            logger.error(f"Error reading schema: {e}")
            raise
    
    @staticmethod
    def get_metadata(path: str):
        """Get metadata of Parquet file"""
        try:
            parquet_file = pq.ParquetFile(path)
            return {
                'num_rows': parquet_file.metadata.num_rows,
                'num_columns': parquet_file.metadata.num_columns,
                'schema': parquet_file.schema,
            }
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            raise
