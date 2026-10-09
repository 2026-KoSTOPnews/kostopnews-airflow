from unittest.mock import call

import pendulum


def test_reaggregate_missing_dates(mocker):
    dates = [
        pendulum.date(2026, 10, 7),
        pendulum.date(2026, 10, 8),
    ]

    mock_get_date_range = mocker.patch(
        "utils.date_utils.get_date_range",
        side_effect=[
            ("start_1", "end_1"),
            ("start_2", "end_2"),
        ],
    )

    mock_aggregate_sentiment = mocker.patch(
        "task.news_sentiment_aggregate_pipeline_tasks.aggregate_sentiment",
        side_effect=[
            [{"result": 1}],
            [{"result": 2}],
        ],
    )

    results = []

    for target_date in dates:
        start_date, end_date = mock_get_date_range(target_date)
        results.extend(
            mock_aggregate_sentiment(
                "DAILY",
                start_date,
                end_date,
            )
        )

    assert mock_get_date_range.call_count == 2

    assert mock_aggregate_sentiment.call_args_list == [
        call("DAILY", "start_1", "end_1"),
        call("DAILY", "start_2", "end_2"),
    ]

    assert len(results) == 2