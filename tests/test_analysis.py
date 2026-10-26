from dags.core.config import settings
from dags.task import news_analysis_pipeline_tasks


def test_store_news_sentiment_batches(monkeypatch):
    """감성 분석 결과의 배치 저장, 오류 제외, 중복 데이터 갱신 및 커밋 여부를 검증한다."""
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

    # analyze_news의 실제 반환 구조
    xcom_result = {
        "sentiment_results": results,
        "keyword_results": [],
    }

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

    def mock_xcom_pull(self, task_ids, key=None):
        captured["task_ids"] = task_ids
        captured["key"] = key
        return xcom_result

    def mock_execute_values(cur, query, rows, page_size):
        captured["rows"] = rows
        captured["page_size"] = page_size
        captured["query"] = query

    monkeypatch.setattr(
        news_analysis_pipeline_tasks,
        "get_db_connection",
        lambda: MockConnection(),
    )
    monkeypatch.setattr(
        news_analysis_pipeline_tasks,
        "execute_values",
        mock_execute_values,
    )

    ti = type(
        "MockTaskInstance",
        (),
        {"xcom_pull": mock_xcom_pull},
    )()

    news_analysis_pipeline_tasks.store_news_sentiment(ti=ti)

    # XCom 조회 검증
    assert captured["task_ids"] == "analyze_news"
    assert captured["key"] == "return_value"

    # 오류 결과 제외 검증
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

    # 배치 저장 및 중복 데이터 갱신 쿼리 검증
    assert captured["page_size"] == 50
    assert "ON CONFLICT (article_id, company_id)" in captured["query"]
    assert "DO UPDATE SET" in captured["query"]

    # 커밋 검증
    assert captured["committed"] is True
    assert "rolled_back" not in captured


def test_save_keywords_batches(monkeypatch):
    """키워드 분석 결과의 배치 저장, 오류·빈 키워드 제외 및 커밋 여부를 검증한다."""
    results = [
        {"article_id": 1, "keywords": ["삼성전자", "반도체"]},
        {"article_id": 2, "keywords": ["AI", "", "  "]},
        {"article_id": 3, "keywords": ["오류 키워드"], "error": "API error"},
    ]

    # analyze_news의 실제 XCom 반환 구조
    xcom_result = {
        "sentiment_results": [],
        "keyword_results": results,
    }

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

    def mock_xcom_pull(self, task_ids, key=None):
        captured["task_ids"] = task_ids
        captured["key"] = key
        return xcom_result

    monkeypatch.setattr(
        news_analysis_pipeline_tasks,
        "get_db_connection",
        lambda: MockConnection(),
    )
    monkeypatch.setattr(
        news_analysis_pipeline_tasks,
        "execute_values",
        mock_execute_values,
    )

    ti = type(
        "MockTaskInstance",
        (),
        {"xcom_pull": mock_xcom_pull},
    )()

    news_analysis_pipeline_tasks.store_news_keywords(ti=ti)

    # XCom 조회 검증
    assert captured["task_ids"] == "analyze_news"
    assert captured["key"] == "return_value"

    # 오류 및 빈 키워드 제외 검증
    assert captured["rows"] == [
        (1, "삼성전자", settings.MODEL_VERSION),
        (1, "반도체", settings.MODEL_VERSION),
        (2, "AI", settings.MODEL_VERSION),
    ]

    # 배치 저장 및 중복 처리 쿼리 검증
    assert captured["page_size"] == 50
    assert "ON CONFLICT (article_id, keyword)" in captured["query"]
    assert "DO NOTHING" in captured["query"]

    # 트랜잭션 커밋 검증
    assert captured["committed"] is True
    assert "rolled_back" not in captured