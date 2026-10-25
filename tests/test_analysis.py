from dags.core.config import settings
from dags.task import news_sentiment_pipeline_tasks
from dags.task import news_keyword_pipeline_tasks


def test_store_news_sentiment_batches(monkeypatch):
    """감성 분석 결과를 배치 단위로 저장하고 오류 결과 제외, 중복 데이터 갱신 및 커밋 여부를 검증한다."""
    results = [
        {
            "article_id": 1,
            "company_id": 10,
            "summary": "반도체 실적 개선",
            "sentiment": "positive",
            "score": 0.9,
        },
        {
            "article_id": 2,
            "company_id": 20,
            "summary": "시장 불확실성 확대",
            "sentiment": "negative",
            "score": -0.7,
        },
        {
            "article_id": 3,
            "company_id": 30,
            "summary": "오류 결과",
            "sentiment": "neutral",
            "score": 0.0,
            "error": "API error",
        },
    ]

    captured = {}

    class MockCursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def cursor(self):
            return MockCursor()

        def commit(self):
            captured["committed"] = True

        def rollback(self):
            captured["rolled_back"] = True

    class MockTaskInstance:
        def xcom_pull(self, task_ids):
            assert task_ids == "call_sentiment_batch"
            return results

    def mock_execute_values(cur, query, rows, page_size):
        captured["rows"] = rows
        captured["page_size"] = page_size
        captured["query"] = query

    monkeypatch.setattr(
        news_sentiment_pipeline_tasks,
        "get_db_connection",
        lambda: MockConnection(),
    )
    monkeypatch.setattr(
        news_sentiment_pipeline_tasks,
        "execute_values",
        mock_execute_values,
    )

    news_sentiment_pipeline_tasks.store_news_sentiment(ti=MockTaskInstance())

    assert captured["rows"] == [
        (
            1, 10, "반도체 실적 개선",
            "positive", 0.9, settings.MODEL_VERSION,
        ),
        (
            2, 20, "시장 불확실성 확대",
            "negative", -0.7, settings.MODEL_VERSION,
        ),
    ]
    assert captured["page_size"] == 50
    assert "ON CONFLICT (article_id, company_id)" in captured["query"]
    assert "DO UPDATE SET" in captured["query"]
    assert captured["committed"] is True


def test_save_keywords_batches(monkeypatch):
    """키워드 분석 결과를 배치 단위로 저장하고 오류·빈 키워드 제외, 중복 키워드 처리 및 커밋 여부를 검증한다."""
    results = [
        {"article_id": 1, "keywords": ["삼성전자", "반도체"]},
        {"article_id": 2, "keywords": ["AI", "", "  "]},
        {"article_id": 3, "keywords": ["오류 키워드"], "error": "API error"},
    ]

    captured = {}

    class MockCursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def cursor(self):
            return MockCursor()

        def commit(self):
            captured["committed"] = True

        def rollback(self):
            captured["rolled_back"] = True

    def mock_execute_values(cur, query, rows, page_size):
        captured["rows"] = rows
        captured["page_size"] = page_size
        captured["query"] = query

    monkeypatch.setattr(
        news_keyword_pipeline_tasks,
        "get_db_connection",
        lambda: MockConnection(),
    )
    monkeypatch.setattr(
        news_keyword_pipeline_tasks,
        "execute_values",
        mock_execute_values,
    )

    news_keyword_pipeline_tasks.store_news_keywords(
        ti=type(
            "MockTaskInstance",
            (),
            {"xcom_pull": lambda self, task_ids: results},
        )()
    )

    assert captured["rows"] == [
        (1, "삼성전자", settings.MODEL_VERSION),
        (1, "반도체", settings.MODEL_VERSION),
        (2, "AI", settings.MODEL_VERSION),
    ]
    assert captured["page_size"] == 50
    assert "ON CONFLICT (article_id, keyword)" in captured["query"]
    assert captured["committed"] is True