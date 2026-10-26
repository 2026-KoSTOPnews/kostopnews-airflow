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
            a.content
        FROM news_articles a
        JOIN news_mentions m ON a.id = m.article_id
        JOIN companies c ON m.company_id = c.id
        LEFT JOIN news_analysis na
            ON na.article_id = a.id
            AND na.company_id = m.company_id
        WHERE na.article_id IS NULL
        ORDER BY a.id, m.company_id
        LIMIT 50;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    sentiment_data = [
        {
            "article_id": article_id,
            "company_id": company_id,
            "company_name": company_name,
            "title": title,
            "content": content,
        }
        for article_id, company_id, company_name, title, content in rows
    ]

    # 키워드는 기사 단위로 추출하므로 article_id 기준 중복 제거
    keyword_data = list({
        item["article_id"]: {
            "article_id": item["article_id"],
            "title": item["title"],
            "content": item["content"],
        }
        for item in reversed(sentiment_data)
    }.values())

    return {
        "sentiment_data": sentiment_data,
        "keyword_data": keyword_data,
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