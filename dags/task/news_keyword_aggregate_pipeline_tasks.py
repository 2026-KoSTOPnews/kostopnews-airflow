from psycopg2.extras import execute_values

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pendulum

from core.database import DB_CONFIG
from core.keywords import COMPANY_KEYWORDS
from core.database import get_db_connection
from utils.date_utils import get_date_range

AGGREGATE_PERIODS = {
    "DAILY": "day",
    "WEEKLY": "week",
    "MONTHLY": "month",
}

# -------------------------
# 키워드 분석 집계
# -------------------------
def aggregate_keyword_periods():
    execution_date = pendulum.now("Asia/Seoul").date()

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
def reaggregate_keyword_periods():
    execution_date = pendulum.now("Asia/Seoul").date()

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

    values = [
        (
            result["company_id"],
            result["period_type"],
            result["period_start"],
            result["keyword"],
            result["count"],
        )
        for result in results
    ]

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                execute_values(
                    cur,
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
                    VALUES %s
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
                    values,
                    template="(%s, %s, %s, %s, %s, NOW(), NOW())",
                    page_size=50,
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

# -------------------------
# 키워드 집계 함수
# -------------------------
def aggregate_keyword(period_type, start_date, end_date):
    period_unit = AGGREGATE_PERIODS[period_type]

    keyword_values = [
        (company_id, keyword)
        for company_id, keywords in COMPANY_KEYWORDS.items()
        for keyword in keywords
    ]

    if not keyword_values:
        return []

    result = []

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            values_query = ", ".join(
                cur.mogrify("(%s, %s)", (company_id, keyword)).decode()
                for company_id, keyword in keyword_values
            )

            query = f"""
                WITH target_keywords(company_id, keyword) AS (
                    VALUES {values_query}
                )
                SELECT
                    tk.company_id,
                    DATE_TRUNC('{period_unit}', a.pub_date)
                        AS period_start,
                    tk.keyword,
                    COUNT(DISTINCT a.id) AS keyword_count
                FROM target_keywords tk
                JOIN news_analysis na
                    ON na.company_id = tk.company_id
                JOIN news_articles a
                    ON a.id = na.article_id
                JOIN news_keywords nk
                    ON nk.article_id = a.id
                WHERE a.pub_date >= %s
                  AND a.pub_date < %s
                  AND nk.keyword IS NOT NULL
                  AND TRIM(nk.keyword) != ''
                  AND nk.keyword ILIKE '%%' || tk.keyword || '%%'
                GROUP BY
                    tk.company_id,
                    DATE_TRUNC('{period_unit}', a.pub_date),
                    tk.keyword
            """

            cur.execute(query, (start_date, end_date))
            rows = cur.fetchall()

            for row in rows:
                result.append({
                    "company_id": row[0],
                    "period_type": period_type,
                    "period_start": row[1],
                    "keyword": row[2],
                    "count": row[3],
                })

    return result