from datetime import datetime

from dags.task.news_sentiment_aggregate_pipeline_tasks import reaggregate_sentiment_periods, store_sentiment_aggregate


def test_reaggregate_sentiment_periods(mocker):
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[]
    )

    # 수요일 -> DAILY만 실행
    context = {
        "logical_date": datetime(2026, 9, 23)
    }

    reaggregate_sentiment_periods(**context)

    assert mock_aggregate.call_count == 1

    calls = mock_aggregate.call_args_list

    # DAILY : 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 9, 18)
    assert calls[0].args[2] == datetime(2026, 9, 19)


def test_reaggregate_sentiment_periods_weekly(mocker):
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[]
    )

    # 토요일 -> DAILY + WEEKLY 실행
    context = {
        "logical_date": datetime(2026, 9, 26)
    }

    reaggregate_sentiment_periods(**context)

    assert mock_aggregate.call_count == 2

    calls = mock_aggregate.call_args_list

    # DAILY : 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 9, 21)
    assert calls[0].args[2] == datetime(2026, 9, 22)

    # WEEKLY : 전주 월~일
    assert calls[1].args[0] == "WEEKLY"
    assert calls[1].args[1] == datetime(2026, 9, 14)
    assert calls[1].args[2] == datetime(2026, 9, 21)


def test_reaggregate_sentiment_periods_monthly(mocker):
    mock_aggregate = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        return_value=[]
    )

    # 10일 -> DAILY + MONTHLY 실행
    context = {
        "logical_date": datetime(2026, 11, 10)
    }

    reaggregate_sentiment_periods(**context)

    assert mock_aggregate.call_count == 2

    calls = mock_aggregate.call_args_list

    # DAILY : 5일 전
    assert calls[0].args[0] == "DAILY"
    assert calls[0].args[1] == datetime(2026, 11, 5)
    assert calls[0].args[2] == datetime(2026, 11, 6)

    # MONTHLY : 지난달 전체
    assert calls[1].args[0] == "MONTHLY"
    assert calls[1].args[1] == datetime(2026, 10, 1)
    assert calls[1].args[2] == datetime(2026, 11, 1)


def test_store_sentiment_aggregate(mocker):
    mock_conn = mocker.patch(
        "dags.task.news_sentiment_aggregate_pipeline_tasks.psycopg2.connect"
    )

    mock_cursor = mock_conn.return_value.cursor.return_value

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
        }
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

    mock_conn.return_value.commit.assert_called_once()