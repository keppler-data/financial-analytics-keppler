# -*- coding: utf-8 -*-
"""
PostgreSQL Database Client
Utilidad para conectar y ejecutar queries en PostgreSQL
"""

import psycopg2
from psycopg2 import sql
import os
from typing import Optional, List, Tuple, Any

class PostgresConnection:
    """
    Cliente de conexión a PostgreSQL
    """
    
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 5432):
        """
        Inicializa conexión a PostgreSQL
        
        Args:
            host: Host de PostgreSQL
            user: Usuario de PostgreSQL
            password: Password de PostgreSQL
            database: Nombre de la base de datos
            port: Puerto (default: 5432)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establece conexión a PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            self.cursor = self.connection.cursor()
            print(f"✅ Conectado a PostgreSQL: {self.database}@{self.host}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {str(e)}")
            return False
    
    def execute(self, query: str, params: Optional[Tuple] = None):
        """
        Ejecuta una query SQL
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
        """
        if not self.connection:
            self.connect()
        
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            print(f"✅ Query ejecutada exitosamente")
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Error ejecutando query: {str(e)}")
            raise
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Ejecuta query y retorna todos los resultados
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
            
        Returns:
            Lista de tuplas con los resultados
        """
        if not self.connection:
            self.connect()
        
        try:
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            print(f"❌ Error ejecutando query: {str(e)}")
            raise
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """
        Ejecuta query y retorna un solo resultado
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
            
        Returns:
            Tupla con el resultado o None
        """
        if not self.connection:
            self.connect()
        
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(f"❌ Error ejecutando query: {str(e)}")
            raise
    
    def close(self):
        """Cierra la conexión a PostgreSQL"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✅ Conexión PostgreSQL cerrada")
