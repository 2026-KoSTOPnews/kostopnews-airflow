from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool

from core.config import settings

DB_CONFIG = {
    "host": settings.POSTGRES_HOST,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}

db_pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_CONFIG,
)

@contextmanager
def get_db_connection():
    conn = db_pool.getconn()

    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        if not conn.closed:
            conn.rollback()
        db_pool.putconn(conn)