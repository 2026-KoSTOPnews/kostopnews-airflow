from datetime import date, datetime

from dags.task.news_keyword_aggregate_pipeline_tasks import aggregate_keyword


def test_aggregate_keyword(test_db):
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        r for r in result
        if r["company_id"] == 1
        and r["keyword"] == "반도체"
    ]

    assert len(samsung) == 1
    assert samsung[0]["count"] == 2


def test_duplicate_keyword_in_same_article_counted_once(test_db):
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        r for r in result
        if r["company_id"] == 1
        and r["keyword"] == "반도체"
    ]

    # 같은 기사에서 '반도체'가 여러 번 매칭되어도
    # 기사 자체는 한 번만 집계되어야 함
    assert samsung[0]["count"] == 2


def test_daily_keyword_period(test_db):
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    assert all(
        r["period_start"].date() == date(2026, 10, 5)
        for r in result
    )


def test_no_keyword_data_for_empty_date(test_db):
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 3),
        datetime(2026, 10, 4),
    )

    assert result == []