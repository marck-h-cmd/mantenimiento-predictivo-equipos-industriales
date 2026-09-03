# config/database.py
# Módulo de conexión y gestión de base de datos PostgreSQL

import psycopg2
import psycopg2.extras
import pandas as pd
from contextlib import contextmanager
from config.settings import DB_CONFIG


class DatabaseManager:
    """Gestor de conexiones y operaciones con PostgreSQL."""

    def __init__(self):
        self.config = DB_CONFIG

    def get_connection(self):
        """Obtiene una conexión a la base de datos."""
        return psycopg2.connect(**self.config)

    @contextmanager
    def get_cursor(self, dict_cursor=False):
        """Context manager para transacciones seguras."""
        conn = self.get_connection()
        cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query, params=None, fetch=True, dict_cursor=False):
        """Ejecuta una consulta SQL y retorna resultados."""
        with self.get_cursor(dict_cursor=dict_cursor) as cursor:
            cursor.execute(query, params)
            if fetch and cursor.description:
                return cursor.fetchall()
            return None

    def execute_many(self, query, params_list):
        """Ejecuta una consulta con múltiples parámetros."""
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)

    def query_to_dataframe(self, query, params=None):
        """Ejecuta consulta y retorna DataFrame de pandas."""
        conn = self.get_connection()
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    def test_connection(self):
        """Verifica la conexión a la base de datos."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return True, version
        except Exception as e:
            return False, str(e)


# Instancia global
db = DatabaseManager()
