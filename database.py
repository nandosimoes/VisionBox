import mysql.connector
from mysql.connector import pooling

from config import Config


class Database:
    """Acesso ao MySQL com pool de conexões."""

    _pool = None

    @classmethod
    def _get_pool(cls):
        if cls._pool is None:
            cls._pool = pooling.MySQLConnectionPool(
                pool_name="visionbox",
                pool_size=5,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset="utf8mb4",
            )
        return cls._pool

    @classmethod
    def consultar(cls, sql, params=(), um=False):
        """SELECT. Retorna lista de dicts, ou um único dict/None se um=True."""
        conn = cls._get_pool().get_connection()
        cur = None
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            linhas = cur.fetchall()
            if um:
                return linhas[0] if linhas else None
            return linhas
        finally:
            if cur:
                cur.close()
            conn.close()

    @classmethod
    def executar(cls, sql, params=()):
        """INSERT/UPDATE/DELETE. Retorna o último id inserido."""
        conn = cls._get_pool().get_connection()
        cur = None
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        except mysql.connector.Error:
            conn.rollback()
            raise
        finally:
            if cur:
                cur.close()
            conn.close()
