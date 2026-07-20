import psycopg2
import requests

from core.config import settings
from core.database import DB_CONFIG

# -------------------------
# 뉴스 데이터 로드
# -------------------------
def fetch_data(**context):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT
            a.id AS article_id,
            m.company_id,
            c.name AS company_name,
            a.title,
            a.content
        FROM news_articles a
        JOIN news_mentions m
            ON a.id = m.article_id
        JOIN companies c
            ON m.company_id = c.id
        WHERE NOT EXISTS (
            SELECT 1
            FROM news_analysis na
            WHERE na.article_id = a.id
              AND na.company_id = m.company_id
        )
        LIMIT 10;
        """

    cur.execute(query)
    rows = cur.fetchall()

    result = []

    for r in rows:
        result.append({
            "article_id": r[0],
            "company_id": r[1],
            "company_name": r[2],
            "title": r[3],
            "content": r[4]
        })

    cur.close()
    conn.close()

    return result

# -------------------------
# 뉴스 분석 결과 저장
# -------------------------
def store_news_sentiment(**context):
    results = context["ti"].xcom_pull(task_ids="call_sentiment_batch")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for r in results:

        if r.get("error"):
            continue

        cur.execute("""
            INSERT INTO news_analysis (
                article_id,
                company_id,
                summary,
                sentiment,
                sentiment_score,
                model_version
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (article_id, company_id)
            DO UPDATE SET
                summary = EXCLUDED.summary,
                sentiment = EXCLUDED.sentiment,
                sentiment_score = EXCLUDED.sentiment_score,
                model_version = EXCLUDED.model_version
        """, (
            r["article_id"],
            r["company_id"],
            r["summary"],
            r["sentiment"],
            r["score"],
            settings.MODEL_VERSION,
        ))

    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# 뉴스 배치 단위 분석
# -------------------------
def call_sentiment_batch(**context):
    data = context["ti"].xcom_pull(task_ids="fetch_data")

    res = requests.post(
        "http://fastapi:8000/sentiment/batch",
        json=data,
        timeout=600
    )

    res.raise_for_status()

    return res.json()