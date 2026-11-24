from datetime import datetime
import pendulum

from unittest.mock import MagicMock

from dags.task.news_sentiment_aggregate_pipeline_tasks import reaggregate_sentiment_periods, store_sentiment_aggregate
from dags.task import news_sentiment_aggregate_pipeline_tasks as sentiment_tasks


def test_reaggregate_sentiment_periods(mocker):
    """일별 감성 분석 집계 실행 및 날짜 범위를 검증한다."""
    mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.pendulum.now",
        return_value=pendulum.datetime(2026, 9, 23, tz="Asia/Seoul"),
    )
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[],
    )

    # 수요일 -> DAILY만 실행
    reaggregate_sentiment_periods()

    assert mock_aggregate.call_count == 1

    calls = mock_aggregate.call_args_list

    # DAILY: 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 9, 18)
    assert calls[0].args[2] == datetime(2026, 9, 19)


def test_reaggregate_sentiment_periods_weekly(mocker):
    """주간 감성 분석 집계 실행 및 날짜 범위를 검증한다."""
    mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.pendulum.now",
        return_value=pendulum.datetime(2026, 9, 26, tz="Asia/Seoul"),
    )
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[],
    )

    # 토요일 -> DAILY + WEEKLY 실행
    reaggregate_sentiment_periods()

    assert mock_aggregate.call_count == 2

    calls = mock_aggregate.call_args_list

    # DAILY: 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 9, 21)
    assert calls[0].args[2] == datetime(2026, 9, 22)

    # WEEKLY: 전주 월~일
    assert calls[1].args[0] == "WEEKLY"
    assert calls[1].args[1] == datetime(2026, 9, 14)
    assert calls[1].args[2] == datetime(2026, 9, 21)


def test_reaggregate_sentiment_periods_monthly(mocker):
    """월간 감성 분석 집계 실행 및 날짜 범위를 검증한다."""
    mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.pendulum.now",
        return_value=pendulum.datetime(2026, 11, 10, tz="Asia/Seoul"),
    )
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[],
    )

    # 매월 10일 -> DAILY + MONTHLY 실행
    reaggregate_sentiment_periods()

    assert mock_aggregate.call_count == 2

    calls = mock_aggregate.call_args_list

    # DAILY: 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 11, 5)
    assert calls[0].args[2] == datetime(2026, 11, 6)

    # MONTHLY: 지난달 전체
    assert calls[1].args[0] == "MONTHLY"
    assert calls[1].args[1] == datetime(2026, 10, 1)
    assert calls[1].args[2] == datetime(2026, 11, 1)


def test_store_sentiment_aggregate(mocker):
    """감성 분석 집계 결과를 기업별로 배치 저장하고 DB 작업을 검증한다."""
    mock_db_connection = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.get_db_connection"
    )

    mock_conn = MagicMock()
    mock_db_connection.return_value.__enter__.return_value = mock_conn

    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    results = [
        {
            "company_id": 1,
            "period_type": "DAILY",
            "period_start": datetime(2026, 9, 16),
            "positive_count": 10,
            "negative_count": 3,
            "neutral_count": 2,
            "sentiment_score": 0.4667,
        }
    ]

    context = {
        "ti": mocker.Mock(),
        "params": {
            "source_task_id": "aggregate_sentiment_periods"
        },
    }

    context["ti"].xcom_pull.return_value = results

    store_sentiment_aggregate(**context)

    mock_cursor.execute.assert_called_once()

    query, params = mock_cursor.execute.call_args.args

    assert "ON CONFLICT" in query
    assert "DO UPDATE SET" in query
    assert "updated_at = NOW()" in query

    assert params == (
        1,
        "DAILY",
        datetime(2026, 9, 16),
        10,
        3,
        2,
        0.4667,
    )

    mock_conn.commit.assert_called_once()


def test_store_sentiment_aggregate(mocker):
    """감성 분석 집계 결과를 기업별로 배치 저장하고 DB 작업을 검증한다."""
    mock_db_connection = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.get_db_connection"
    )

    mock_execute_values = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.execute_values"
    )

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_db_connection.return_value.__enter__.return_value = mock_conn

    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    results = [
        {
            "company_id": 1,
            "period_type": "DAILY",
            "period_start": datetime(2026, 9, 16),
            "positive_count": 10,
            "negative_count": 3,
            "neutral_count": 2,
            "sentiment_score": 0.4667,
        },
        {
            "company_id": 2,
            "period_type": "DAILY",
            "period_start": datetime(2026, 9, 16),
            "positive_count": 5,
            "negative_count": 4,
            "neutral_count": 1,
            "sentiment_score": 0.1,
        },
    ]

    context = {
        "ti": mocker.Mock(),
        "params": {
            "source_task_id": "aggregate_sentiment_periods",
        },
    }

    context["ti"].xcom_pull.return_value = results

    sentiment_tasks.store_sentiment_aggregate(**context)

    mock_execute_values.assert_called_once()

    call_args = mock_execute_values.call_args
    query = call_args.args[1]
    values = call_args.args[2]

    assert "ON CONFLICT" in query
    assert "DO UPDATE SET" in query
    assert "updated_at = NOW()" in query

    assert values == [
        (
            1,
            "DAILY",
            datetime(2026, 9, 16),
            10,
            3,
            2,
            0.4667,
        ),
        (
            2,
            "DAILY",
            datetime(2026, 9, 16),
            5,
            4,
            1,
            0.1,
        ),
    ]

    assert call_args.kwargs["page_size"] == 50

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()