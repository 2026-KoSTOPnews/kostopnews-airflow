from unittest.mock import MagicMock

import pytest
from psycopg2.pool import PoolError

import dags.core.database as database


def test_getconn_with_wait_returns_connection_immediately(monkeypatch):
    """사용 가능한 연결이 있으면 즉시 반환한다."""
    conn = MagicMock()

    pool = MagicMock()
    pool.getconn.return_value = conn
    monkeypatch.setattr(database, "get_db_pool", lambda: pool)

    result = database.getconn_with_wait()

    assert result is conn
    pool.getconn.assert_called_once()


def test_getconn_with_wait_retries_until_connection_available(monkeypatch):
    """풀이 가득 찼다가 연결이 반환되면 재시도 후 획득한다."""
    conn = MagicMock()

    pool = MagicMock()
    pool.getconn.side_effect = [
        PoolError("connection pool exhausted"),
        conn,
    ]
    monkeypatch.setattr(database, "get_db_pool", lambda: pool)

    # 테스트에서는 실제로 대기하지 않는다.
    monkeypatch.setattr(database.time, "sleep", lambda _: None)

    # 첫 호출은 마감 시간 계산, 두 번째는 남은 시간 계산
    times = iter([0, 0])
    monkeypatch.setattr(
        database.time,
        "monotonic",
        lambda: next(times),
    )

    result = database.getconn_with_wait(
        timeout=30,
        retry_interval=0.1,
    )

    assert result is conn
    assert pool.getconn.call_count == 2


def test_getconn_with_wait_raises_timeout(monkeypatch):
    """제한 시간 내에 연결을 얻지 못하면 TimeoutError를 발생시킨다."""
    pool = MagicMock()
    pool.getconn.side_effect = PoolError("connection pool exhausted")
    monkeypatch.setattr(database, "get_db_pool", lambda: pool)

    # 마감 시간 계산은 0초, 이후에는 31초가 경과한 것으로 설정
    times = iter([0, 31])
    monkeypatch.setattr(
        database.time,
        "monotonic",
        lambda: next(times),
    )

    with pytest.raises(TimeoutError, match="30 seconds"):
        database.getconn_with_wait(timeout=30)

    pool.getconn.assert_called_once()


def test_get_db_connection_returns_connection_to_pool(monkeypatch):
    """작업이 끝나면 연결을 풀에 반환한다."""
    conn = MagicMock()
    conn.closed = False

    pool = MagicMock()
    monkeypatch.setattr(database, "get_db_pool", lambda: pool)
    monkeypatch.setattr(
        database,
        "getconn_with_wait",
        lambda: conn,
    )

    with database.get_db_connection() as acquired_conn:
        assert acquired_conn is conn

    pool.putconn.assert_called_once_with(conn)


def test_get_db_connection_rolls_back_on_exception(monkeypatch):
    """DB 작업 중 예외가 발생하면 롤백 후 연결을 반환한다."""
    conn = MagicMock()
    conn.closed = False

    pool = MagicMock()
    monkeypatch.setattr(database, "get_db_pool", lambda: pool)
    monkeypatch.setattr(
        database,
        "getconn_with_wait",
        lambda: conn,
    )

    with pytest.raises(ValueError, match="query failed"):
        with database.get_db_connection():
            raise ValueError("query failed")

    conn.rollback.assert_called_once()
    pool.putconn.assert_called_once_with(conn)