#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL Database Client
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PostgresClient:
    """PostgreSQL database operations wrapper"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("Connected to PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Closed database connection")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert record into table"""
        columns = list(data.keys())
        values = list(data.values())
        
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
            sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                self.conn.commit()
                logger.info(f"Inserted record into {table}")
                return cur.rowcount
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error inserting record: {e}")
            raise
    
    def execute_update(self, table: str, data: Dict[str, Any], where: str) -> int:
        """Update records in table"""
        columns = list(data.keys())
        values = list(data.values())
        
        set_clause = sql.SQL(', ').join(
            sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder())
            for col in columns
        )
        
        query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
            sql.Identifier(table),
            set_clause,
            sql.SQL(where)
        )
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, values)
                self.conn.commit()
                logger.info(f"Updated {cur.rowcount} records in {table}")
                return cur.rowcount
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error updating records: {e}")
            raise
