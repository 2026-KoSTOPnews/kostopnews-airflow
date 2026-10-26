from psycopg2.extras import execute_values

from core.config import settings
from core.database import get_db_connection

from services.news_analysis_service import fetch_news_data
from services.news_analysis_service import request_sentiment_analysis
from services.news_analysis_service import request_keyword_extraction

# -------------------------
# 뉴스 분석 실행
# -------------------------
def analyze_news():
    news_data = fetch_news_data()

    sentiment_results = request_sentiment_analysis(news_data["sentiment_data"])

    keyword_results = request_keyword_extraction(news_data["keyword_data"])

    return {
        "sentiment_results": sentiment_results,
        "keyword_results": keyword_results,
    }

# -------------------------
# 뉴스 감성 분석 결과 저장
# -------------------------
def store_news_sentiment(**context):
    results = context["ti"].xcom_pull(
        task_ids="analyze_news",
        key="return_value",
    )

    if not results:
        return

    sentiment_results = results.get("sentiment_results", [])

    if not sentiment_results:
        return

    rows = []

    for r in sentiment_results:
        if r.get("error"):
            continue

        rows.append((
            r["article_id"],
            r["company_id"],
            r["summary"],
            r["sentiment"],
            r["score"],
            settings.MODEL_VERSION,
        ))

    if not rows:
        return

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO news_analysis (
                        article_id,
                        company_id,
                        summary,
                        sentiment,
                        sentiment_score,
                        model_version
                    )
                    VALUES %s
                    ON CONFLICT (article_id, company_id)
                    DO UPDATE SET
                        summary = EXCLUDED.summary,
                        sentiment = EXCLUDED.sentiment,
                        sentiment_score = EXCLUDED.sentiment_score,
                        model_version = EXCLUDED.model_version
                    """,
                    rows,
                    page_size=50,
                )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

# -------------------------
# 뉴스 키워드 저장
# -------------------------
def store_news_keywords(**context):
    results = context["ti"].xcom_pull(
        task_ids="analyze_news",
        key="return_value",
    )

    if not results:
        return

    keyword_results = results.get("keyword_results", [])

    if not keyword_results:
        return

    rows = []

    for r in keyword_results:
        if r.get("error"):
            continue

        article_id = r["article_id"]

        for keyword in r.get("keywords", []):
            if not keyword or not keyword.strip():
                continue

            rows.append((
                article_id,
                keyword.strip(),
                settings.MODEL_VERSION,
            ))

    if not rows:
        return

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO news_keywords (
                        article_id,
                        keyword,
                        model_version
                    )
                    VALUES %s
                    ON CONFLICT (article_id, keyword)
                    DO NOTHING
                    """,
                    rows,
                    page_size=50,
                )

            conn.commit()
        except Exception:
            conn.rollback()
            raise