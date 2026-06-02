#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Schema utilities and validation
"""

from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Schema validation utilities"""
    
    @staticmethod
    def load_schema(path: str) -> Dict[str, Any]:
        """Load schema from JSON file"""
        try:
            with open(path, 'r') as f:
                schema = json.load(f)
            logger.info(f"Loaded schema from {path}")
            return schema
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            raise
    
    @staticmethod
    def validate_schema(data: List[Dict], schema: Dict[str, Any]) -> bool:
        """Validate data against schema"""
        try:
            required_columns = schema.get('required', [])
            column_types = schema.get('columns', {})
            
            for row in data:
                # Check required columns
                for col in required_columns:
                    if col not in row or row[col] is None:
                        logger.error(f"Missing required column: {col}")
                        return False
                
                # Check column types
                for col, expected_type in column_types.items():
                    if col in row and row[col] is not None:
                        actual_type = type(row[col]).__name__
                        if actual_type != expected_type:
                            logger.warning(
                                f"Type mismatch for {col}: "
                                f"expected {expected_type}, got {actual_type}"
                            )
            
            logger.info("Schema validation passed")
            return True
        except Exception as e:
            logger.error(f"Error validating schema: {e}")
            raise
    
    @staticmethod
    def compare_schemas(schema1: Dict, schema2: Dict) -> Dict[str, List[str]]:
        """Compare two schemas and return differences"""
        cols1 = set(schema1.get('columns', {}).keys())
        cols2 = set(schema2.get('columns', {}).keys())
        
        return {
            'only_in_first': list(cols1 - cols2),
            'only_in_second': list(cols2 - cols1),
            'in_both': list(cols1 & cols2),
        }
