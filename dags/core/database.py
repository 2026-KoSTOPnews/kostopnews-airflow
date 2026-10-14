import time
from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool, PoolError

from core.config import settings

import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": settings.POSTGRES_HOST,
    "database": settings.POSTGRES_DB,
    "user": settings.POSTGRES_USER,
    "password": settings.POSTGRES_PASSWORD,
    "port": settings.POSTGRES_PORT,
}

db_pool = None

def get_db_pool():
    global db_pool

    if db_pool is None:
        db_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=7,
            **DB_CONFIG,
        )

    return db_pool

def getconn_with_wait(timeout=30, retry_interval=0.1):
    deadline = time.monotonic() + timeout
    pool = get_db_pool()

    while True:
        try:
            return pool.getconn()
        except PoolError as exc:
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                logger.error(
                    "DB connection pool exhausted: "
                    "failed to acquire a connection within %s seconds",
                    timeout,
                )
                raise TimeoutError(
                    f"DB connection unavailable after {timeout} seconds"
                ) from exc

            time.sleep(min(retry_interval, remaining))

@contextmanager
def get_db_connection():
    pool = get_db_pool()
    conn = getconn_with_wait()

    try:
        yield conn
    finally:
        try:
            if not conn.closed:
                # 커밋되지 않은 트랜잭션을 정리
                conn.rollback()
        finally:
            pool.putconn(conn)