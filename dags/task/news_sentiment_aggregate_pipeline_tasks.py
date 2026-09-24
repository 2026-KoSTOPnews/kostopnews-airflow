from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import psycopg2

from core.database import DB_CONFIG

from utils.date_utils import get_date_range

AGGREGATE_PERIODS = {
    "DAILY": "day",
    "WEEKLY": "week",
    "MONTHLY": "month",
}

# -------------------------
# 감정 분석 집계
# -------------------------
def aggregate_sentiment_periods(**context):
    execution_date = context["logical_date"].date()

    results = []

    # -------------------------
    # DAILY : 어제
    # -------------------------
    daily_date = execution_date - timedelta(days=1)
    daily_start, daily_end = get_date_range(daily_date)

    results.extend(
        aggregate_sentiment(
            "DAILY",
            daily_start,
            daily_end
        )
    )

    # -------------------------
    # WEEKLY : 지난주
    # 월요일에만 실행
    # -------------------------
    if execution_date.weekday() == 0:
        weekly_end = execution_date
        weekly_start = weekly_end - timedelta(days=7)

        results.extend(
            aggregate_sentiment(
                "WEEKLY",
                datetime.combine(
                    weekly_start,
                    datetime.min.time()
                ),
                datetime.combine(
                    weekly_end,
                    datetime.min.time()
                )
            )
        )

    # -------------------------
    # MONTHLY : 지난달
    # 매월 1일에 실행
    # -------------------------
    if execution_date.day == 1:
        monthly_end = execution_date
        monthly_start = monthly_end - relativedelta(months=1)

        results.extend(
            aggregate_sentiment(
                "MONTHLY",
                datetime.combine(
                    monthly_start,
                    datetime.min.time()
                ),
                datetime.combine(
                    monthly_end,
                    datetime.min.time()
                )
            )
        )

    return results

# -------------------------
# 감정 분석 재집계
# -------------------------
def reaggregate_sentiment_periods(**context):
    execution_date = context["logical_date"].date()

    results = []

    # -------------------------
    # DAILY : 5일 전 하루만 재집계
    # -------------------------
    daily_date = execution_date - timedelta(days=5)
    daily_start, daily_end = get_date_range(daily_date)

    results.extend(
        aggregate_sentiment(
            "DAILY",
            daily_start,
            daily_end
        )
    )

    # -------------------------
    # WEEKLY : 전주
    # 토요일에만 재집계
    # -------------------------
    if execution_date.weekday() == 5:
        weekly_end = execution_date - timedelta(days=5)
        weekly_start = weekly_end - timedelta(days=7)

        results.extend(
            aggregate_sentiment(
                "WEEKLY",
                datetime.combine(
                    weekly_start,
                    datetime.min.time()
                ),
                datetime.combine(
                    weekly_end,
                    datetime.min.time()
                )
            )
        )

    # -------------------------
    # MONTHLY : 지난달
    # 매월 10일에 재집계
    # -------------------------
    if execution_date.day == 10:
        monthly_end = execution_date.replace(day=1)
        monthly_start = monthly_end - relativedelta(months=1)

        results.extend(
            aggregate_sentiment(
                "MONTHLY",
                datetime.combine(
                    monthly_start,
                    datetime.min.time()
                ),
                datetime.combine(
                    monthly_end,
                    datetime.min.time()
                )
            )
        )

    return results

# -------------------------
# 집계 결과 저장
# -------------------------
def store_sentiment_aggregate(**context):
    source_task_id = context["params"]["source_task_id"]

    results = context["ti"].xcom_pull(task_ids=source_task_id)

    if not results:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for result in results:
        cur.execute(
            """
            INSERT INTO news_sentiment_aggregate (
                company_id,
                period_type,
                period_start,
                positive_count,
                negative_count,
                neutral_count,
                sentiment_score
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (
                company_id,
                period_type,
                period_start
            )
            DO UPDATE SET
                positive_count = EXCLUDED.positive_count,
                negative_count = EXCLUDED.negative_count,
                neutral_count = EXCLUDED.neutral_count,
                sentiment_score = EXCLUDED.sentiment_score,
                updated_at = NOW()
            """,
            (
                result["company_id"],
                result["period_type"],
                result["period_start"],
                result["positive_count"],
                result["negative_count"],
                result["neutral_count"],
                result["sentiment_score"],
            )
        )

    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# 감정 분석 집계 함수
# -------------------------
def aggregate_sentiment(period_type, start_date, end_date):
    period_unit = AGGREGATE_PERIODS[period_type]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = f"""
        SELECT
            na.company_id,
            DATE_TRUNC('{period_unit}', a.pub_date) AS period_start,
            COUNT(*) FILTER (
                WHERE LOWER(na.sentiment) = 'positive'
            ) AS positive_count,
            COUNT(*) FILTER (
                WHERE LOWER(na.sentiment) = 'negative'
            ) AS negative_count,
            COUNT(*) FILTER (
                WHERE LOWER(na.sentiment) = 'neutral'
            ) AS neutral_count
        FROM news_analysis na
        JOIN news_articles a
            ON na.article_id = a.id
        WHERE a.pub_date >= %s
          AND a.pub_date < %s
        GROUP BY
            na.company_id,
            DATE_TRUNC('{period_unit}', a.pub_date)
    """

    cur.execute(query, (start_date, end_date))

    rows = cur.fetchall()

    result = []

    for row in rows:
        company_id = row[0]
        period_start = row[1]

        positive_count = row[2] or 0
        negative_count = row[3] or 0
        neutral_count = row[4] or 0

        total_count = positive_count + negative_count + neutral_count
        sentiment_score = (positive_count - negative_count) / total_count if total_count > 0 else 0.0

        result.append({
            "company_id": company_id,
            "period_type": period_type,
            "period_start": period_start,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "sentiment_score": sentiment_score,
        })

    cur.close()
    conn.close()

    return result