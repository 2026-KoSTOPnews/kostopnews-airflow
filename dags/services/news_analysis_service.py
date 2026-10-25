import requests

from core.config import settings
from core.database import get_db_connection

# -------------------------
# 분석 대상 뉴스 조회
# -------------------------
def fetch_news_data():
    query = """
        SELECT
            a.id AS article_id,
            m.company_id,
            c.name AS company_name,
            a.title,
            a.content,
            (na.article_id IS NULL) AS needs_sentiment,
            (
                EXISTS (
                    SELECT 1
                    FROM news_analysis existing_na
                    WHERE existing_na.article_id = a.id
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM news_keywords nk
                    WHERE nk.article_id = a.id
                )
            ) AS needs_keywords
        FROM news_articles a
        JOIN news_mentions m ON a.id = m.article_id
        JOIN companies c ON m.company_id = c.id
        LEFT JOIN news_analysis na
            ON na.article_id = a.id
            AND na.company_id = m.company_id
        WHERE
            na.article_id IS NULL
            OR (
                EXISTS (
                    SELECT 1
                    FROM news_analysis existing_na
                    WHERE existing_na.article_id = a.id
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM news_keywords nk
                    WHERE nk.article_id = a.id
                )
            )
        ORDER BY a.id, m.company_id
        LIMIT 50;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    sentiment_data = []
    keyword_data = {}

    for row in rows:
        (
            article_id,
            company_id,
            company_name,
            title,
            content,
            needs_sentiment,
            needs_keywords,
        ) = row

        if needs_sentiment:
            sentiment_data.append({
                "article_id": article_id,
                "company_id": company_id,
                "company_name": company_name,
                "title": title,
                "content": content,
            })

        if needs_keywords:
            keyword_data[article_id] = {
                "article_id": article_id,
                "title": title,
                "content": content,
            }

    return {
        "sentiment_data": sentiment_data,
        "keyword_data": list(keyword_data.values()),
    }

# -------------------------
# 감성 분석 API 호출
# -------------------------
def request_sentiment_analysis(sentiment_data):
    if not sentiment_data:
        return []

    response = requests.post(
        f"{settings.FASTAPI_BASE_URL}/sentiment/batch",
        json=sentiment_data,
        timeout=600,
    )
    response.raise_for_status()

    return response.json()

# -------------------------
# 키워드 추출 API 호출
# -------------------------
def request_keyword_extraction(keyword_data):
    if not keyword_data:
        return []

    response = requests.post(
        f"{settings.FASTAPI_BASE_URL}/keywords/batch",
        json=keyword_data,
        timeout=600,
    )
    response.raise_for_status()

    return response.json()