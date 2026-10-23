from unittest.mock import MagicMock

import pytest

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


def test_get_articles_only_selects_unprocessed(mock_db):
    """미처리 기사만 조회하는 SQL인지 확인."""
    cursor, _ = mock_db

    cursor.fetchall.return_value = [
        (
            1,
            "삼성전자 실적 발표",
            "https://example.com/1",
            "기사 내용",
            "test",
        )
    ]

    articles = db_service.get_articles_for_company_extraction(
        limit=50
    )

    sql = cursor.execute.call_args.args[0]

    assert "company_extraction_processed = FALSE" in sql
    assert "LIMIT %s" in sql
    assert articles == [
        {
            "id": 1,
            "title": "삼성전자 실적 발표",
            "link": "https://example.com/1",
            "content": "기사 내용",
            "source": "test",
        }
    ]


def test_get_articles_returns_empty_list(mock_db):
    """미처리 기사가 없으면 빈 목록 반환."""
    cursor, _ = mock_db
    cursor.fetchall.return_value = []

    result = db_service.get_articles_for_company_extraction()

    assert result == []


def test_mark_articles_processed(mock_db):
    """지정한 기사 ID들을 완료 처리하고 커밋."""
    cursor, connection = mock_db

    db_service.mark_articles_processed([1, 2, 3])

    sql, params = cursor.execute.call_args.args

    assert "SET company_extraction_processed = TRUE" in sql
    assert params == ([1, 2, 3],)
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()


def test_mark_articles_processed_with_empty_ids(mock_db):
    """ID가 없으면 DB 작업을 하지 않음."""
    cursor, connection = mock_db

    db_service.mark_articles_processed([])

    cursor.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_mark_articles_processed_rolls_back_on_error(mock_db):
    """완료 처리 SQL 실패 시 롤백하고 예외 전달."""
    cursor, connection = mock_db
    cursor.execute.side_effect = RuntimeError("DB 오류")

    with pytest.raises(RuntimeError, match="DB 오류"):
        db_service.mark_articles_processed([1, 2])

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_store_articles_returns_empty_for_no_input(mock_db):
    """저장할 기사가 없으면 빈 목록 반환."""
    cursor, connection = mock_db

    result = db_service.store_articles([])

    assert result == []
    cursor.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_store_articles_inserts_and_returns_ids(mock_db):
    """기사 저장 후 ID와 기본 정보를 반환."""
    cursor, connection = mock_db
    cursor.fetchone.side_effect = [(101,), (102,)]

    articles = [
        {
            "title": "기사 1",
            "link": "https://example.com/1",
            "source": "test",
            "content": "내용 1",
        },
        {
            "title": "기사 2",
            "link": "https://example.com/2",
            "source": "test",
            "content": "내용 2",
        },
    ]

    result = db_service.store_articles(articles)

    assert [item["id"] for item in result] == [101, 102]
    assert len(result) == 2
    assert cursor.execute.call_count == 2
    connection.commit.assert_called_once()


def test_store_articles_rolls_back_on_error(mock_db):
    """기사 저장 중 오류가 나면 롤백."""
    cursor, connection = mock_db
    cursor.execute.side_effect = RuntimeError("INSERT 실패")

    articles = [
        {
            "title": "기사",
            "link": "https://example.com/1",
            "source": "test",
            "content": "내용",
        }
    ]

    with pytest.raises(RuntimeError, match="INSERT 실패"):
        db_service.store_articles(articles)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_store_company_mentions_with_empty_input(mock_db):
    """저장할 매칭 결과가 없으면 DB 작업을 하지 않음."""
    cursor, connection = mock_db

    db_service.store_company_mentions([])

    cursor.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_store_company_mentions_inserts_multiple_companies(mock_db):
    """한 기사에 여러 기업의 매칭 결과를 저장."""
    cursor, connection = mock_db
    cursor.fetchall.return_value = [
        (101, "https://example.com/1")
    ]

    data = [
        {
            "article": {
                "link": "https://example.com/1",
            },
            "matches": [
                {"company_id": 1, "score": 0.8},
                {"company_id": 2, "score": 0.9},
            ],
        }
    ]

    db_service.store_company_mentions(data)

    # 첫 번째 쿼리는 기사 ID 조회,
    # 다음 두 쿼리는 기업별 mention INSERT
    assert cursor.execute.call_count == 3
    connection.commit.assert_called_once()

    insert_calls = [
        c for c in cursor.execute.call_args_list
        if "INSERT INTO news_mentions" in c.args[0]
    ]

    assert len(insert_calls) == 2
    assert insert_calls[0].args[1] == (101, 1, 0.8)
    assert insert_calls[1].args[1] == (101, 2, 0.9)


def test_store_company_mentions_rolls_back_on_error(mock_db):
    """기업 언급 저장 중 오류가 나면 롤백."""
    cursor, connection = mock_db
    cursor.execute.side_effect = RuntimeError("INSERT 실패")

    data = [
        {
            "article": {"link": "https://example.com/1"},
            "matches": [{"company_id": 1, "score": 0.8}],
        }
    ]

    with pytest.raises(RuntimeError, match="INSERT 실패"):
        db_service.store_company_mentions(data)

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()