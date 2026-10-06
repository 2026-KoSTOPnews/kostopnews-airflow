from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import psycopg2

from core.database import DB_CONFIG
from core.keywords import COMPANY_KEYWORDS
from utils.date_utils import get_date_range

AGGREGATE_PERIODS = {
    "DAILY": "day",
    "WEEKLY": "week",
    "MONTHLY": "month",
}

# -------------------------
# 키워드 분석 집계
# -------------------------
def aggregate_keyword_periods(**context):
    execution_date = context["logical_date"].date()

    results = []

    # -------------------------
    # DAILY : 어제
    # -------------------------
    daily_date = execution_date - timedelta(days=1)
    daily_start, daily_end = get_date_range(daily_date)

    results.extend(
        aggregate_keyword(
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
            aggregate_keyword(
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
        monthly_start = (monthly_end.replace(day=1) - timedelta(days=1)).replace(day=1)

        results.extend(
            aggregate_keyword(
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
# 키워드 분석 재집계
# -------------------------
def reaggregate_keyword_periods(**context):
    execution_date = context["logical_date"].date()

    results = []

    # -------------------------
    # DAILY : 5일 전 하루만 재집계
    # -------------------------
    daily_date = execution_date - timedelta(days=5)
    daily_start, daily_end = get_date_range(daily_date)

    results.extend(
        aggregate_keyword(
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
            aggregate_keyword(
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
            aggregate_keyword(
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
# 키워드 집계 결과 저장
# -------------------------
def store_keyword_aggregate(**context):
    source_task_id = context["params"]["source_task_id"]

    results = context["ti"].xcom_pull(task_ids=source_task_id)

    if not results:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for result in results:
        cur.execute(
            """
            INSERT INTO news_keyword_aggregate (
                company_id,
                period_type,
                period_start,
                keyword,
                count,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (
                company_id,
                period_type,
                period_start,
                keyword
            )
            DO UPDATE SET
                count = EXCLUDED.count,
                updated_at = NOW()
            """,
            (
                result["company_id"],
                result["period_type"],
                result["period_start"],
                result["keyword"],
                result["count"],
            )
        )

    conn.commit()

    cur.close()
    conn.close()

# -------------------------
# 키워드 집계 함수
# -------------------------
def aggregate_keyword(period_type, start_date, end_date):
    period_unit = AGGREGATE_PERIODS[period_type]

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    result = []

    for company_id, keywords in COMPANY_KEYWORDS.items():
        for keyword in keywords:
            query = f"""
                SELECT
                    %s AS company_id,
                    DATE_TRUNC('{period_unit}', a.pub_date) AS period_start,
                    %s AS keyword,
                    COUNT(DISTINCT a.id) AS keyword_count
                FROM news_keywords nk
                JOIN news_articles a
                    ON nk.article_id = a.id
                JOIN news_analysis na
                    ON nk.article_id = na.article_id
                WHERE na.company_id = %s
                  AND a.pub_date >= %s
                  AND a.pub_date < %s
                  AND nk.keyword IS NOT NULL
                  AND TRIM(nk.keyword) != ''
                  AND nk.keyword ILIKE %s
                GROUP BY
                    DATE_TRUNC('{period_unit}', a.pub_date)
            """
            cur.execute(
                query,
                (
                    company_id,
                    keyword,
                    company_id,
                    start_date,
                    end_date,
                    f"%{keyword}%",
                )
            )

            rows = cur.fetchall()

            for row in rows:
                result.append({
                    "company_id": row[0],
                    "period_type": period_type,
                    "period_start": row[1],
                    "keyword": row[2],
                    "count": row[3],
                })

    cur.close()
    conn.close()

    return result