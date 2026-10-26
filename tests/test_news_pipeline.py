from datetime import datetime
from unittest.mock import MagicMock

import services.postgres_service as postgres_service
import task.news_pipeline_tasks as news_pipeline_tasks


def test_fetch_and_store_news(monkeypatch):
    """뉴스 수집부터 중복 제거, 본문 수집, 저장까지의 실행 순서를 검증한다."""
    calls = []

    articles = [
        {
            "title": "삼성전자 실적 발표",
            "link": "https://example.com/1",
        }
    ]

    companies = {
        "Samsung": {
            "id": 1,
            "aliases": ["삼성전자"],
        }
    }

    def mock_fetch_rss():
        calls.append("fetch_rss")
        return articles

    def mock_load_companies():
        calls.append("load_companies")
        return companies

    def mock_deduplicate_articles(articles, companies):
        calls.append("deduplicate_articles")
        return articles

    def mock_fetch_article_content(articles):
        calls.append("fetch_article_content")
        return articles

    def mock_store_articles(articles):
        calls.append("store_articles")

    monkeypatch.setattr(
        news_pipeline_tasks,
        "fetch_rss",
        mock_fetch_rss,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "load_companies",
        mock_load_companies,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "deduplicate_articles",
        mock_deduplicate_articles,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "fetch_article_content",
        mock_fetch_article_content,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "store_articles",
        mock_store_articles,
    )

    news_pipeline_tasks.fetch_and_store_news()

    assert calls == [
        "fetch_rss",
        "load_companies",
        "deduplicate_articles",
        "fetch_article_content",
        "store_articles",
    ]


def test_store_articles_batches(monkeypatch):
    """뉴스 기사를 배치 저장하고 반환값과 DB 작업을 검증한다."""
    mock_db_connection = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_db_connection.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr(
        postgres_service,
        "get_db_connection",
        mock_db_connection,
    )

    mock_execute_values = MagicMock()
    monkeypatch.setattr(
        postgres_service,
        "execute_values",
        mock_execute_values,
    )

    mock_cursor.fetchall.return_value = [
        (1, "삼성전자 실적 발표", "https://example.com/1", "연합뉴스"),
        (2, "네이버 실적 발표", "https://example.com/2", "한국경제"),
    ]

    articles = [
        {
            "title": "삼성전자 실적 발표",
            "link": "https://example.com/1",
            "pub_date": "2026-10-25T09:00:00",
            "source": "연합뉴스",
            "content": "삼성전자 실적 관련 기사",
        },
        {
            "title": "네이버 실적 발표",
            "link": "https://example.com/2",
            "pub_date": None,
            "source": "한국경제",
            "content": "네이버 실적 관련 기사",
        },
    ]

    result = news_pipeline_tasks.store_articles(articles)

    mock_execute_values.assert_called_once()

    call_args = mock_execute_values.call_args
    query = call_args.args[1]
    values = call_args.args[2]

    assert "INSERT INTO news_articles" in query
    assert "ON CONFLICT (link)" in query
    assert "RETURNING id, title, link, source" in query

    assert values == [
        (
            "삼성전자 실적 발표",
            "https://example.com/1",
            datetime(2026, 10, 25, 9, 0),
            "연합뉴스",
            "삼성전자 실적 관련 기사",
        ),
        (
            "네이버 실적 발표",
            "https://example.com/2",
            None,
            "한국경제",
            "네이버 실적 관련 기사",
        ),
    ]

    assert call_args.kwargs["page_size"] == news_pipeline_tasks.BATCH_SIZE

    assert result == [
        {
            "id": 1,
            "title": "삼성전자 실적 발표",
            "link": "https://example.com/1",
            "source": "연합뉴스",
        },
        {
            "id": 2,
            "title": "네이버 실적 발표",
            "link": "https://example.com/2",
            "source": "한국경제",
        },
    ]

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_store_articles_empty():
    """저장할 기사가 없으면 DB 작업 없이 빈 리스트를 반환한다."""
    result = news_pipeline_tasks.store_articles([])

    assert result == []