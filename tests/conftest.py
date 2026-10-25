import pytest

from unittest.mock import MagicMock

from dags.services import postgres_service as db_service


@pytest.fixture
def mock_db(monkeypatch):
    """DB 연결과 커서를 모킹."""
    cursor = MagicMock()
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    context = MagicMock()
    context.__enter__.return_value = connection

    monkeypatch.setattr(
        db_service,
        "get_db_connection",
        lambda: context,
    )

    return cursor, connection